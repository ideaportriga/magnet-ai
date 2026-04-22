from abc import ABC, abstractmethod

from ..models import ChunkerResult, ContentConfig


class AbstractChunker(ABC):
    def __init__(self, config: ContentConfig) -> None:
        self.config = config

    @abstractmethod
    async def chunk_text(
        self,
        text: str,
        *,
        document_title: str | None = None,
        source_url: str | None = None,
    ) -> ChunkerResult:
        """Chunk the text and return chunks with optional document metadata.

        Concrete chunkers may use ``source_url`` to resolve relative URLs in
        the produced chunk content against the original source page.
        """
