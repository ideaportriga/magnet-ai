import logging
import re
from typing import Any, override

from kreuzberg import ChunkingConfig, ExtractionConfig, extract_bytes

from core.db.models.knowledge_graph import KnowledgeGraphChunk

from ..models import ChunkerResult, ContentConfig
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)

# Regex to find the last [Page: N] marker before or within a chunk
_PAGE_MARKER_RE = re.compile(r"\[Page:\s*(\d+)\]")


class KreuzbergChunker(AbstractChunker):
    """Deterministic Markdown-aware chunker powered by Kreuzberg.

    Uses Kreuzberg's built-in ChunkingConfig for Markdown-aware splitting
    with configurable chunk size and overlap.
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @override
    async def chunk_text(
        self, text: str, *, document_title: str | None = None
    ) -> ChunkerResult:
        if not text or not text.strip():
            logger.info("Empty text provided to DeterministicRecursiveChunker")
            return ChunkerResult(chunks=[], document_metadata=None)

        options = self.config.chunker.get("options", {})
        chunk_size = int(options.get("chunk_max_size", 18000))
        chunk_overlap_ratio = float(options.get("recursive_chunk_overlap", 0.1))
        chunk_overlap = int(chunk_size * chunk_overlap_ratio)

        extraction_config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=chunk_size,
                max_overlap=chunk_overlap,
            ),
        )

        result = await extract_bytes(
            text.encode("utf-8"), "text/markdown", config=extraction_config
        )

        logger.info(
            "Split document into %d chunks using Kreuzberg markdown chunker",
            len(result.chunks),
        )

        title_pattern = options.get("chunk_title_pattern") or ""
        chunks: list[KnowledgeGraphChunk] = []

        for idx, kreuzberg_chunk in enumerate(result.chunks):
            chunk_content = kreuzberg_chunk.content

            # Extract page number from the last [Page: N] marker in the chunk
            page_matches = _PAGE_MARKER_RE.findall(chunk_content)
            page = int(page_matches[-1]) if page_matches else None

            default_title = f"Chunk {idx + 1}"
            title = (
                _format_title_pattern(
                    title_pattern,
                    {
                        "index": idx + 1,
                        "page": page if page is not None else -1,
                        "type": "TEXT",
                        "toc_reference": "",
                        "llm_title": "",
                    },
                )
                if title_pattern
                else default_title
            )

            chunk = KnowledgeGraphChunk(
                generated_id=f"chunk_{idx}",
                chunk_type="TEXT",
                title=title,
                toc_reference="",
                page=page,
                content=chunk_content,
                embedded_content=chunk_content,
            )
            chunks.append(chunk)

        return ChunkerResult(chunks=chunks)


def _format_title_pattern(pattern: str, values: dict[str, Any]) -> str:
    return re.sub(r"{(\w+)}", lambda m: str(values.get(m.group(1), "")), pattern)
