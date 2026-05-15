from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import chunks_table_name
from services.observability.decorators import observe, observability_context

from .chunk_text_compressor import compress_for_skip_detection

logger = logging.getLogger(__name__)

ContentFieldPreference = Literal["content", "embedded_content"]
DEFAULT_SEGMENT_SIZE = 18000
DEFAULT_SEGMENT_OVERLAP = 0.1
DEFAULT_RELEVANCE_FILTER_CONCURRENCY = 8
_DECISION_TOKENS = ("KEEP:DIRECT", "KEEP:CONTEXT", "SKIP")


class ChunkDocumentReader:
    """Loaded, in-memory view of a document reconstructed from chunk rows.

    Internal helper for context-extraction code paths (e.g. LLM metadata
    and entity extraction). Not exposed as a ContentReader and not part of
    the ingestion pipeline. Caller manages the surrounding transaction. Use
    :meth:`load` to read chunks once, then ask the instance for the required
    representation.

    Overlap regions between consecutive chunks (when the chunker configured
    overlap) are not deduplicated -- the chunk row does not persist overlap
    size. Downstream segmenters re-window the joined text anyway, so this
    only inflates the segmenter input slightly.
    """

    def __init__(
        self,
        *,
        graph_id: UUID,
        document_id: str,
        chunks: Sequence[str],
        separator: str = "\n\n",
    ) -> None:
        self.graph_id = graph_id
        self.document_id = document_id
        self._chunks = tuple(
            str(chunk).strip() for chunk in chunks if str(chunk or "").strip()
        )
        self._separator = separator
        self._text: str | None = None
        self._segments_by_options: dict[tuple[int, float], list[str]] = {}
        self._filtered_chunk_count: int = 0

    @classmethod
    async def load(
        cls,
        db_session: AsyncSession,
        *,
        graph_id: UUID,
        document_id: str,
        separator: str = "\n\n",
        prefer_field: ContentFieldPreference = "content",
    ) -> "ChunkDocumentReader":
        """Read document chunks once and return an in-memory reader instance."""
        chunks_tbl = chunks_table_name(graph_id)

        if prefer_field == "content":
            content_expr = "COALESCE(NULLIF(content, ''), NULLIF(embedded_content, ''))"
        else:
            content_expr = "COALESCE(NULLIF(embedded_content, ''), NULLIF(content, ''))"

        res = await db_session.execute(
            text(
                f"""
                SELECT {content_expr} AS content
                FROM {chunks_tbl}
                WHERE document_id = CAST(:doc_id AS uuid)
                ORDER BY index NULLS FIRST, created_at
                """
            ),
            {"doc_id": document_id},
        )
        return cls(
            graph_id=graph_id,
            document_id=document_id,
            chunks=[str(v).strip() for v in res.scalars().all() if v],
            separator=separator,
        )

    def as_chunks(self) -> list[str]:
        """Return chunk content in persisted order."""
        return list(self._chunks)

    def as_text(self) -> str:
        """Return the document's reconstructed text, or "" if no chunk content exists."""
        if self._text is None:
            self._text = self._separator.join(self._chunks)
        return self._text

    @property
    def filtered_chunk_count(self) -> int:
        """How many chunks the most recent filter_irrelevant_chunks call dropped."""
        return self._filtered_chunk_count

    async def filter_irrelevant_chunks(
        self,
        *,
        enabled: bool,
        entity_definitions: Sequence[Any],
        prompt_template_system_name: str,
        cancel_check: Callable[[], Awaitable[bool]] | None = None,
        max_concurrency: int = DEFAULT_RELEVANCE_FILTER_CONCURRENCY,
    ) -> "ChunkDocumentReader":
        """Drop chunks the relevance-filter LLM classifies as SKIP.

        No-op when disabled, when there are no chunks, or when entity_definitions
        is empty. Returns self so callers can chain ``.as_segments(...)``.

        Failure-mode: on any per-chunk error (LLM error, unparseable response),
        the chunk is **kept**. Quality dominates cost in the ambiguous case.
        """
        if (
            not enabled
            or not self._chunks
            or not prompt_template_system_name
            or not entity_definitions
        ):
            return self

        await self._apply_relevance_filter(
            entity_definitions=entity_definitions,
            prompt_template_system_name=prompt_template_system_name,
            cancel_check=cancel_check,
            max_concurrency=max_concurrency,
        )
        return self

    @observe(
        name="Preparation: relevance filter", channel="production", source="production"
    )
    async def _apply_relevance_filter(
        self,
        *,
        entity_definitions: Sequence[Any],
        prompt_template_system_name: str,
        cancel_check: Callable[[], Awaitable[bool]] | None = None,
        max_concurrency: int = DEFAULT_RELEVANCE_FILTER_CONCURRENCY,
    ) -> None:
        total_chunks = len(self._chunks)

        observability_context.update_current_span(
            input={
                "Document Id": self.document_id,
                "Total Chunks": total_chunks,
            }
        )

        # Deferred imports to avoid a circular import with
        # services.knowledge_graph.llm_entity_extraction (which imports this class).
        from services.knowledge_graph.llm_entity_extraction import (
            build_entity_extraction_prompt_schema_markdown,
        )

        schema_text = build_entity_extraction_prompt_schema_markdown(
            list(entity_definitions)
        )

        kept = await _classify_and_filter_chunks(
            chunks=self._chunks,
            schema_text=schema_text,
            prompt_template_system_name=prompt_template_system_name,
            cancel_check=cancel_check,
            max_concurrency=max(1, int(max_concurrency)),
        )

        self._filtered_chunk_count = len(self._chunks) - len(kept)
        if self._filtered_chunk_count:
            logger.info(
                "Relevance filter for document %s: kept %d/%d chunks",
                self.document_id,
                len(kept),
                len(self._chunks),
            )
        self._chunks = tuple(kept)
        self._text = None
        self._segments_by_options.clear()

        observability_context.update_current_span(
            output={
                "Kept Chunks": len(kept),
                "Filtered Chunks": self._filtered_chunk_count,
            }
        )

    def as_segments(
        self,
        *,
        segment_size: int = DEFAULT_SEGMENT_SIZE,
        segment_overlap: float = DEFAULT_SEGMENT_OVERLAP,
    ) -> list[str]:
        """Return reconstructed document text split into overlapping segments."""
        seg_size = self._normalize_segment_size(segment_size)
        overlap_ratio = self._normalize_segment_overlap(segment_overlap)
        cache_key = (seg_size, overlap_ratio)
        if cache_key not in self._segments_by_options:
            self._segments_by_options[cache_key] = self._split_text_into_segments(
                self.as_text(),
                segment_size=seg_size,
                segment_overlap=overlap_ratio,
            )
        return list(self._segments_by_options[cache_key])

    def _split_text_into_segments(
        self,
        text_value: str,
        *,
        segment_size: int,
        segment_overlap: float,
    ) -> list[str]:
        text_value = str(text_value or "")
        if not text_value:
            return []

        if len(text_value) <= segment_size:
            return [text_value]

        overlap_size = int(segment_size * segment_overlap)
        step_size = max(segment_size - overlap_size, 1)

        segments: list[str] = []
        start = 0
        while start < len(text_value):
            end = min(start + segment_size, len(text_value))
            segments.append(text_value[start:end])
            if end >= len(text_value):
                break
            start += step_size
        return segments

    def _normalize_segment_size(self, segment_size: int) -> int:
        try:
            seg_size = int(segment_size)
        except Exception:
            seg_size = DEFAULT_SEGMENT_SIZE
        return max(seg_size, 100)

    def _normalize_segment_overlap(self, segment_overlap: float) -> float:
        try:
            overlap_ratio = float(segment_overlap)
        except Exception:
            overlap_ratio = DEFAULT_SEGMENT_OVERLAP
        return max(0.0, min(overlap_ratio, 0.9))


def _parse_filter_decision(raw: str) -> str:
    """Extract the decision token (KEEP:DIRECT | KEEP:CONTEXT | SKIP) from the
    last non-empty line of the LLM response. Returns "" on parse failure so
    callers can fail-open (keep the chunk).
    """
    if not isinstance(raw, str):
        return ""
    last_line = ""
    for line in reversed(raw.splitlines()):
        stripped = line.strip().strip("`").strip()
        if stripped:
            last_line = stripped
            break
    if not last_line:
        return ""
    upper = last_line.upper()
    for token in _DECISION_TOKENS:
        if token in upper:
            return token
    return ""


async def _classify_and_filter_chunks(
    *,
    chunks: Sequence[str],
    schema_text: str,
    prompt_template_system_name: str,
    cancel_check: Callable[[], Awaitable[bool]] | None,
    max_concurrency: int,
) -> list[str]:
    from services.prompt_templates import execute_prompt_template

    semaphore = asyncio.Semaphore(max_concurrency)
    decisions: list[bool] = [True] * len(chunks)

    async def _classify(index: int, chunk: str) -> None:
        if cancel_check and await cancel_check():
            return
        compressed = compress_for_skip_detection(chunk)
        # Empty/very short compressed output -> not enough signal to judge.
        # Fail-open: keep the chunk.
        if len(compressed) < 16:
            return
        async with semaphore:
            if cancel_check and await cancel_check():
                return
            try:
                result = await execute_prompt_template(
                    system_name_or_config=prompt_template_system_name,
                    template_values={"SCHEMA": schema_text},
                    template_additional_messages=[
                        {"role": "user", "content": compressed}
                    ],
                )
                token = _parse_filter_decision(getattr(result, "content", ""))
                if token == "SKIP":
                    decisions[index] = False
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Relevance filter call failed for chunk %d: %s. Keeping chunk.",
                    index,
                    exc,
                )

    await asyncio.gather(
        *(_classify(i, chunk) for i, chunk in enumerate(chunks)),
        return_exceptions=False,
    )

    return [chunk for chunk, keep in zip(chunks, decisions) if keep]
