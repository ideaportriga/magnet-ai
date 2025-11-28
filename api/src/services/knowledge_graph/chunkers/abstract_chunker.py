from abc import ABC, abstractmethod

from ..models import ChunkerResult, ContentConfig


class AbstractChunker(ABC):
    def __init__(self, config: ContentConfig) -> None:
        self.config = config

    @abstractmethod
    async def chunk_text(self, text: str) -> ChunkerResult:
        """Chunk the text and return chunks with optional document metadata."""
