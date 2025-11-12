from abc import ABC, abstractmethod

from langchain.schema.document import Document

from services.prompt_templates import execute_prompt_template


class AbstractSplitter(ABC):
    def __init__(self, chunking_config: dict | None = None):
        self.chunking_config = chunking_config or {}

    @abstractmethod
    def split(self) -> list[Document]:
        pass

    async def prepare_chunk(
        self,
        document_content: str,
        chunk_content: str,
        metadata: dict,
        chunk_number: int,
        chunks_total: int,
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
        main_title = metadata.get("title", "Untitled")
        chunk_title = f"{main_title} ({chunk_number}/{chunks_total})"
        metadata = {
            **metadata,
            "chunkTitle": chunk_title,
            "chunkNumber": chunk_number,
            "chunksTotal": chunks_total,
            "content": {
                "unmodified": chunk_content,
                "retrieval": chunk_content_for_retrieval,
            },
        }

        return Document(page_content=chunk_content_to_index, metadata=metadata)
