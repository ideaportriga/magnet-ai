from logging import getLogger
from typing import override

from langchain.schema.document import Document
from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from data_sync.models import ChunkingStrategy
from data_sync.splitters.abstract_splitter import AbstractSplitter
from data_sync.utils import clean_text, parse_page

logger = getLogger(__name__)

DEFAULT_HTML_CHUNK_SIZE = 12000
DEFAULT_HTML_CHUNK_OVERLAP = 2000


class HtmlSplitter(AbstractSplitter):
    def __init__(
        self,
        html: str,
        *,
        base_url: str,
        base_metadata: dict | None = None,
        chunking_config: dict | None = None,
    ):
        self.html = html
        self.base_url = base_url
        self.base_metadata = dict(
            {
                **(base_metadata or {}),
                "type": "html",
            },
        )
        self.chunking_config = chunking_config or {}

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
                        f"Invalid chunk size: {chunk_size}, using default value: {DEFAULT_HTML_CHUNK_SIZE}"
                    )
                    chunk_size = DEFAULT_HTML_CHUNK_SIZE
            else:
                chunk_size = DEFAULT_HTML_CHUNK_SIZE

            chunk_overlap = self.chunking_config.get("chunk_overlap")
            if chunk_overlap:
                try:
                    chunk_overlap = int(chunk_overlap)
                except ValueError:
                    logger.warning(
                        f"Invalid chunk overlap: {chunk_overlap}, using default value: {DEFAULT_HTML_CHUNK_OVERLAP}"
                    )
                    chunk_overlap = DEFAULT_HTML_CHUNK_OVERLAP
            else:
                chunk_overlap = DEFAULT_HTML_CHUNK_OVERLAP

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            raw_chunks = splitter.split_documents(
                [
                    Document(
                        page_content=parse_page(self.html, self.base_url),
                        metadata=self.base_metadata,
                    )
                ]
            )
            raw_chunks = [
                Document(
                    page_content=clean_text(chunk.page_content), metadata=chunk.metadata
                )
                for chunk in raw_chunks
            ]
        # If strategy is None, use the html as is
        elif strategy == ChunkingStrategy.NONE:
            raw_chunks = [
                Document(
                    page_content=clean_text(parse_page(self.html, self.base_url)),
                    metadata=self.base_metadata,
                )
            ]
        elif strategy == ChunkingStrategy.HTML_HEADER_SPLITTING:
            splitter = HTMLHeaderTextSplitter(
                headers_to_split_on=[
                    ("h1", "Header 1"),
                    ("h2", "Header 2"),
                    ("h3", "Header 3"),
                    ("h4", "Header 4"),
                    ("h5", "Header 5"),
                    ("h6", "Header 6"),
                ],
                return_each_element=False,
            )
            raw_chunks = splitter.split_text(self.html)
            raw_chunks = self.__process_html_headers(raw_chunks)
        else:
            raise ValueError(f"Invalid chunking strategy: {strategy} for HTML splitter")

        document_content = "\n\n".join([chunk.page_content for chunk in raw_chunks])
        chunks_total = len(raw_chunks)

        chunks = []
        for i, chunk in enumerate(raw_chunks):
            chunks.append(
                await self.prepare_chunk(
                    document_content=document_content,
                    chunk_content=chunk.page_content,
                    metadata=chunk.metadata,
                    chunk_number=(i + 1),
                    chunks_total=chunks_total,
                )
            )
        return chunks

    def __process_html_headers(self, chunks: list[Document]) -> list[Document]:
        processed_chunks: list[Document] = []

        for chunk in chunks:
            header_1 = chunk.metadata.pop("Header 1", None)
            header_2 = chunk.metadata.pop("Header 2", None)
            header_3 = chunk.metadata.pop("Header 3", None)
            header_4 = chunk.metadata.pop("Header 4", None)
            header_5 = chunk.metadata.pop("Header 5", None)
            header_6 = chunk.metadata.pop("Header 6", None)

            # Skip if the chunk is a header
            if chunk.page_content in [
                header_1,
                header_2,
                header_3,
                header_4,
                header_5,
                header_6,
            ]:
                continue

            # Add headers to the chunk
            content = ""
            if header_1:
                content += f"# {header_1}\n"
            if header_2:
                content += f"## {header_2}\n"
            if header_3:
                content += f"### {header_3}\n"
            if header_4:
                content += f"#### {header_4}\n"
            if header_5:
                content += f"##### {header_5}\n"
            if header_6:
                content += f"###### {header_6}\n"
            content += chunk.page_content

            processed_chunks.append(
                Document(page_content=content, metadata=self.base_metadata)
            )

        return processed_chunks
