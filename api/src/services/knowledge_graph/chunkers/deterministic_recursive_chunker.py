import logging
import re
from typing import Any, override

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.db.models.knowledge_graph import KnowledgeGraphChunk

from ..models import ChunkerResult, ContentConfig
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)


class DeterministicRecursiveChunker(AbstractChunker):
    """Deterministic recursive splitter with embeddings generation.

    Uses RecursiveCharacterTextSplitter with configurable separators, chunk size,
    and overlap. Generates embeddings for each chunk using the configured model
    or a default if unspecified.
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @override
    async def chunk_text(self, text: str) -> ChunkerResult:
        if not text or not text.strip():
            logger.info("Empty text provided to DeterministicRecursiveChunker")
            return ChunkerResult(chunks=[], document_metadata=None)

        options = self.config.chunker.get("options", {})
        chunk_size = int(
            options.get("recursive_chunk_size", options.get("chunk_max_size", 18000))
        )
        chunk_overlap_ratio = float(options.get("recursive_chunk_overlap", 0.1))
        chunk_overlap = int(chunk_size * chunk_overlap_ratio)
        separators = options.get("splitters", ["\n\n", "\n", " ", ""])

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
        )
        text_chunks = splitter.split_text(text)
        logger.info(
            f"Split document into {len(text_chunks)} chunks using recursive splitter"
        )

        chunks: list[KnowledgeGraphChunk] = []
        for idx, chunk_text in enumerate(text_chunks):
            # Resolve title pattern
            options = self.config.chunker.get("options", {})
            pattern = options.get("chunk_title_pattern") or ""

            def format_pattern(pat: str, values: dict[str, Any]) -> str:
                return re.sub(
                    r"{(\w+)}", lambda m: str(values.get(m.group(1), "")), pat
                )

            default_title = f"Chunk {idx + 1}"
            title = (
                format_pattern(
                    pattern,
                    {
                        "index": idx + 1,
                        "page": -1,
                        "type": "TEXT",
                        "toc_reference": "",
                        "llm_title": "",
                    },
                )
                if pattern
                else default_title
            )

            chunk = KnowledgeGraphChunk(
                generated_id=f"chunk_{idx}",
                chunk_type="TEXT",
                title=title,
                toc_reference="",
                content=chunk_text,
                embedded_content=chunk_text,
            )
            chunks.append(chunk)

        return ChunkerResult(chunks=chunks)
