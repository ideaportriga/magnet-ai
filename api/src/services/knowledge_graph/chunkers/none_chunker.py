import logging
from typing import override

from core.db.models.knowledge_graph import KnowledgeGraphChunk

from ..models import ChunkerResult, ContentConfig
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)


class NoneChunker(AbstractChunker):
    """No-op chunker.

    Always returns exactly one chunk containing the original text. The
    indexing layer splits the chunk into parts when its length exceeds
    ``embedding_max_size``.
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @override
    async def chunk_text(
        self,
        text: str,
        *,
        document_title: str | None = None,
        source_url: str | None = None,
    ) -> ChunkerResult:
        content = text or ""

        chunk = KnowledgeGraphChunk(
            chunk_type="TEXT",
            title=document_title,
            content=content,
            embedded_content=content,
        )

        logger.info("NoneChunker produced 1 chunk (len=%s)", len(content))
        return ChunkerResult(chunks=[chunk])
