import asyncio

from langchain.schema.document import Document
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data_sync.utils import clean_text
from services.prompt_templates import execute_prompt_template

DEFAULT_PDF_CHUNK_SIZE = 12000
DEFAULT_PDF_CHUNK_OVERLAP = 2000


class PdfSplitter:
    def __init__(
        self,
        file_path: str,
        base_metadata: dict,
        chunking_config: dict | None = None,
    ):
        self.file_path = file_path
        self.base_metadata = dict(
            {
                **base_metadata,
                "type": "pdf",
            },
        )
        self.chunking_config = chunking_config or {}

    async def split(self) -> list[Document]:
        raw_chunks: list[Document] = []

        strategy = self.chunking_config.get("strategy")
        # If strategy is None, concatenate all pages into one string, separated by newlines
        if strategy == "none":
            raw_chunks = await asyncio.to_thread(PyPDFLoader(self.file_path).load)
            if len(raw_chunks) > 0:
                content = "\n\n".join([chunk.page_content for chunk in raw_chunks])
                metadata = raw_chunks[0].metadata.copy()
                del metadata["page"]
                raw_chunks = [
                    Document(page_content=clean_text(content), metadata=metadata)
                ]
        # If strategy is Recursive Character Text Splitting, use recommended langchain text splitter
        elif strategy == "recursive_character_text_splitting" or not strategy:
            raw_chunks = await asyncio.to_thread(
                lambda: PyPDFLoader(self.file_path).load_and_split(
                    text_splitter=RecursiveCharacterTextSplitter(
                        chunk_size=self.chunking_config.get("chunk_size")
                        or DEFAULT_PDF_CHUNK_SIZE,
                        chunk_overlap=self.chunking_config.get("chunk_overlap")
                        or DEFAULT_PDF_CHUNK_OVERLAP,
                    ),
                )
            )
            raw_chunks = [
                Document(
                    page_content=clean_text(chunk.page_content),
                    metadata=chunk.metadata,
                )
                for chunk in raw_chunks
            ]

        document_content = "\n\n".join([chunk.page_content for chunk in raw_chunks])
        chunks_total = len(raw_chunks)

        return [
            await self.__prepare_chunk(
                document_content=document_content,
                chunk_content=chunk.page_content,
                base_metadata=self.base_metadata,
                chunk_number=(i + 1),
                chunks_total=chunks_total,
                page_number=(chunk.metadata.get("page", 0) + 1)
                if chunk.metadata.get("page") is not None
                else None,
            )
            for i, chunk in enumerate(raw_chunks)
        ]

    async def __prepare_chunk(
        self,
        document_content: str,
        chunk_content: str,
        base_metadata: dict,
        chunk_number: int,
        chunks_total: int,
        page_number: int | None = None,
    ) -> Document:
        chunk_content_to_index = chunk_content
        chunk_content_for_retrieval = chunk_content

        # LLM preprocessing if needed
        if self.chunking_config.get("transformation_enabled"):
            transformed_chunk_content = chunk_content

            prompt_template_system_name = self.chunking_config.get(
                "transformation_prompt_template",
            )
            if prompt_template_system_name:
                llm_response = await execute_prompt_template(
                    system_name_or_config=prompt_template_system_name,
                    template_values={
                        "DOCUMENT": document_content,
                        "CHUNK": chunk_content,
                    },
                    template_additional_messages=[
                        {"role": "user", "content": chunk_content},
                    ],
                )

                if self.chunking_config.get("transformation_method") == "replace":
                    transformed_chunk_content = llm_response.content
                elif self.chunking_config.get("transformation_method") == "append":
                    transformed_chunk_content = (
                        f"{chunk_content}\n\n{llm_response.content}"
                    )
                elif self.chunking_config.get("transformation_method") == "prepend":
                    transformed_chunk_content = (
                        f"{llm_response.content}\n\n{chunk_content}"
                    )

                if self.chunking_config.get("chunk_usage_method") == "transformed_both":
                    chunk_content_to_index = transformed_chunk_content
                    chunk_content_for_retrieval = transformed_chunk_content
                elif (
                    self.chunking_config.get("chunk_usage_method")
                    == "original_indexing_transformed_retrieval"
                ):
                    chunk_content_to_index = chunk_content
                    chunk_content_for_retrieval = transformed_chunk_content
                elif (
                    self.chunking_config.get("chunk_usage_method")
                    == "transformed_indexing_original_retrieval"
                ):
                    chunk_content_to_index = transformed_chunk_content
                    chunk_content_for_retrieval = chunk_content

        # Metadata processing
        main_title = base_metadata.get("title", "Untitled")
        chunk_title = f"{main_title} ({chunk_number}/{chunks_total})"
        source = f"{base_metadata.get('source')}{f'#page={page_number}' if page_number is not None else ''}"
        metadata = {
            **base_metadata,
            "pageNumber": page_number,
            "chunkTitle": chunk_title,
            "chunkNumber": chunk_number,
            "chunksTotal": chunks_total,
            "source": source,
            "content": {
                "unmodified": chunk_content,
                "retrieval": chunk_content_for_retrieval,
            },
        }

        return Document(
            page_content=chunk_content_to_index,
            metadata=metadata,
        )
