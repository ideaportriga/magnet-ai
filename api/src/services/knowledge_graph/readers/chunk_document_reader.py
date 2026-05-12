from __future__ import annotations

from collections.abc import Sequence
from typing import Literal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import chunks_table_name

ContentFieldPreference = Literal["content", "embedded_content"]
DEFAULT_SEGMENT_SIZE = 18000
DEFAULT_SEGMENT_OVERLAP = 0.1


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
