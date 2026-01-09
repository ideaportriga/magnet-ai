import logging
from typing import override

from core.db.models.knowledge_graph import KnowledgeGraphChunk

from ..models import ChunkerResult, ContentConfig
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)


class NoneChunker(AbstractChunker):
    """No-op chunker.

    Always returns exactly one chunk containing the original text (truncated to the
    configured `chunk_max_size`).
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @override
    async def chunk_text(self, text: str) -> ChunkerResult:
        options = (self.config.chunker or {}).get("options", {}) if self.config else {}
        try:
            chunk_max_size = int(options.get("chunk_max_size", 18000))
        except Exception:  # noqa: BLE001
            chunk_max_size = 18000

        if chunk_max_size < 0:
            chunk_max_size = 0

        truncated = text[:chunk_max_size] if text is not None else ""

        # NOTE: We set `embedded_content` to the same value so embedding generation
        # works consistently across strategies.
        chunk = KnowledgeGraphChunk(
            chunk_type="TEXT",
            content=truncated,
            embedded_content=truncated,
        )

        logger.info(
            "NoneChunker produced 1 chunk (len=%s, max=%s)",
            len(truncated),
            chunk_max_size,
        )
        return ChunkerResult(chunks=[chunk])
