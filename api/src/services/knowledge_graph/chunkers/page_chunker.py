import logging
import re
from typing import Any, override

from core.db.models.knowledge_graph import KnowledgeGraphChunk

from ..models import ChunkerResult, ContentConfig
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)

_PAGE_MARKER_RE = re.compile(r"\[Page:\s*(\d+)\]")


class PageChunker(AbstractChunker):
    """Page-based chunker for paged readers (PyPDF, Kreuzberg, LiteParse).

    Splits text on ``[Page: N]`` markers emitted by paged readers and produces
    one chunk per page, with the chunk's ``page`` field populated from the
    marker. Falls back to a single chunk (NoneChunker semantics) when no page
    markers are present.
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @override
    async def chunk_text(
        self, text: str, *, document_title: str | None = None
    ) -> ChunkerResult:
        if not text or not text.strip():
            logger.info("Empty text provided to PageChunker")
            return ChunkerResult(chunks=[], document_metadata=None)

        options = (self.config.chunker or {}).get("options", {}) if self.config else {}
        try:
            chunk_max_size = int(options.get("chunk_max_size", 18000))
        except Exception:  # noqa: BLE001
            chunk_max_size = 18000
        if chunk_max_size < 0:
            chunk_max_size = 0

        title_pattern = options.get("chunk_title_pattern") or ""

        markers = list(_PAGE_MARKER_RE.finditer(text))

        if not markers:
            logger.warning(
                "PageChunker invoked on text with no [Page: N] markers; "
                "falling back to a single chunk"
            )
            truncated = text[:chunk_max_size]
            title = _resolve_title(
                title_pattern,
                idx=0,
                page=None,
                default=document_title or "Chunk 1",
            )
            chunk = KnowledgeGraphChunk(
                generated_id="chunk_0",
                chunk_type="TEXT",
                title=title,
                toc_reference="",
                content=truncated,
                embedded_content=truncated,
            )
            return ChunkerResult(chunks=[chunk])

        segments: list[tuple[int | None, str]] = []

        preamble = text[: markers[0].start()]
        if preamble.strip():
            segments.append((None, preamble))

        for i, marker in enumerate(markers):
            page_number = int(marker.group(1))
            content_start = marker.end()
            content_end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            segment_content = text[content_start:content_end]
            if segment_content.strip():
                segments.append((page_number, segment_content))

        chunks: list[KnowledgeGraphChunk] = []
        for idx, (page, segment) in enumerate(segments):
            content = segment.strip("\n")
            if len(content) > chunk_max_size:
                logger.warning(
                    "PageChunker truncating page %s content from %d to %d chars",
                    page if page is not None else "<preamble>",
                    len(content),
                    chunk_max_size,
                )
                content = content[:chunk_max_size]

            default_title = f"Page {page}" if page is not None else f"Chunk {idx + 1}"
            title = _resolve_title(
                title_pattern,
                idx=idx,
                page=page,
                default=default_title,
            )

            chunk = KnowledgeGraphChunk(
                generated_id=f"chunk_{idx}",
                chunk_type="TEXT",
                title=title,
                toc_reference="",
                page=page,
                content=content,
                embedded_content=content,
            )
            chunks.append(chunk)

        logger.info("PageChunker produced %d chunks from page markers", len(chunks))
        return ChunkerResult(chunks=chunks)


def _resolve_title(pattern: str, *, idx: int, page: int | None, default: str) -> str:
    if not pattern:
        return default
    return _format_title_pattern(
        pattern,
        {
            "index": idx + 1,
            "page": page if page is not None else -1,
            "type": "TEXT",
            "toc_reference": "",
            "llm_title": "",
        },
    )


def _format_title_pattern(pattern: str, values: dict[str, Any]) -> str:
    return re.sub(r"{(\w+)}", lambda m: str(values.get(m.group(1), "")), pattern)
