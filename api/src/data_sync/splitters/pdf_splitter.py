import asyncio
from logging import getLogger
from typing import override

from langchain.schema.document import Document
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data_sync.models import ChunkingStrategy
from data_sync.splitters.abstract_splitter import AbstractSplitter
from data_sync.utils import clean_text

logger = getLogger(__name__)

DEFAULT_PDF_CHUNK_SIZE = 12000
DEFAULT_PDF_CHUNK_OVERLAP = 2000


class PdfSplitter(AbstractSplitter):
    def __init__(
        self,
        file_path: str,
        *,
        base_metadata: dict | None = None,
        chunking_config: dict | None = None,
    ):
        super().__init__(chunking_config)
        self.file_path = file_path
        self.base_metadata = dict(
            {
                **(base_metadata or {}),
                "type": "pdf",
            },
        )

    @override
    async def split(self) -> list[Document]:
        raw_chunks: list[Document] = []

        strategy = self.chunking_config.get("strategy")

        # If strategy is Recursive Character Text Splitting, use recommended langchain text splitter
        # Default strategy
        if (
            not strategy
            or strategy == ChunkingStrategy.RECURSIVE_CHARACTER_TEXT_SPLITTING
        ):
            chunk_size = self.chunking_config.get("chunk_size")
            if chunk_size:
                try:
                    chunk_size = int(chunk_size)
                except ValueError:
                    logger.warning(
                        f"Invalid chunk size: {chunk_size}, using default value: {DEFAULT_PDF_CHUNK_SIZE}"
                    )
                    chunk_size = DEFAULT_PDF_CHUNK_SIZE
            else:
                chunk_size = DEFAULT_PDF_CHUNK_SIZE

            chunk_overlap = self.chunking_config.get("chunk_overlap")
            if chunk_overlap:
                try:
                    chunk_overlap = int(chunk_overlap)
                except ValueError:
                    logger.warning(
                        f"Invalid chunk overlap: {chunk_overlap}, using default value: {DEFAULT_PDF_CHUNK_OVERLAP}"
                    )
                    chunk_overlap = DEFAULT_PDF_CHUNK_OVERLAP
            else:
                chunk_overlap = DEFAULT_PDF_CHUNK_OVERLAP

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            raw_chunks = await asyncio.to_thread(
                lambda: PyPDFLoader(self.file_path).load_and_split(
                    text_splitter=splitter
                )
            )
            raw_chunks = [
                Document(
                    page_content=clean_text(chunk.page_content), metadata=chunk.metadata
                )
                for chunk in raw_chunks
            ]
        # If strategy is None, concatenate all pages into one string, separated by newlines
        elif strategy == ChunkingStrategy.NONE:
            raw_chunks = await asyncio.to_thread(PyPDFLoader(self.file_path).load)
            if len(raw_chunks) > 0:
                content = "\n\n".join([chunk.page_content for chunk in raw_chunks])
                metadata = raw_chunks[0].metadata.copy()
                del metadata["page"]
                raw_chunks = [
                    Document(page_content=clean_text(content), metadata=metadata)
                ]
        else:
            raise ValueError(f"Invalid chunking strategy: {strategy} for PDF splitter")

        document_content = "\n\n".join([chunk.page_content for chunk in raw_chunks])
        chunks_total = len(raw_chunks)

        chunks = []
        for i, chunk in enumerate(raw_chunks):
            page_number = (
                (chunk.metadata.get("page", 0) + 1)
                if chunk.metadata.get("page") is not None
                else None
            )
            chunks.append(
                await self.prepare_chunk(
                    document_content=document_content,
                    chunk_content=chunk.page_content,
                    metadata={
                        **self.base_metadata,
                        "pageNumber": page_number,
                        "source": f"{self.base_metadata.get('source')}{f'#page={page_number}' if page_number is not None else ''}",
                    },
                    chunk_number=(i + 1),
                    chunks_total=chunks_total,
                )
            )
        return chunks
