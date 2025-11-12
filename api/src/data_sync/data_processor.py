from abc import abstractmethod

from bs4 import BeautifulSoup
from langchain.schema import Document
from markdownify import markdownify as md
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

from data_sources.data_source import DataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sources.types.incremental_update_data import IncrementalUpdateData
from models import DocumentData


class DataProcessor:
    @property
    @abstractmethod
    def data_source(self) -> DataSource: ...

    @abstractmethod
    async def load_data(self) -> None: ...

    @abstractmethod
    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]: ...

    @abstractmethod
    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]: ...

    def is_record_unchanged(
        self,
        record_basic_metadata: SourceBasicMetadata,
        document: dict,
    ) -> bool:
        return document.get("modifiedTime") == record_basic_metadata.modified_date

    def get_incremental_update_data(
        self,
        source_basic_metadata: list[SourceBasicMetadata],
        existing_documents: list[dict],
    ) -> IncrementalUpdateData:
        source_records_by_id = {
            metadata.source_id: metadata for metadata in source_basic_metadata
        }

        document_ids = [document.get("id", "") for document in existing_documents]
        grouped_documents_by_record_id = self.__group_documents_by_source_id(
            existing_documents,
        )

        unchanged_record_ids = self.__get_unchanged_record_ids(
            source_records_by_id,
            grouped_documents_by_record_id,
        )

        unchanged_document_ids = self.__get_document_ids_for_records(
            grouped_documents_by_record_id,
            unchanged_record_ids,
        )

        document_ids_to_delete = list(set(document_ids) - set(unchanged_document_ids))

        record_ids_to_add = list(
            set(source_records_by_id.keys()) - unchanged_record_ids,
        )

        return IncrementalUpdateData(record_ids_to_add, document_ids_to_delete)

    def create_documents_from_html(
        self,
        html: str,
        base_metadata: dict,
    ) -> list[DocumentData]:
        if not html:
            return []

        text = self._html_to_text(html)

        return self.create_documents_from_plain_text(text, base_metadata)

    def create_documents_from_plain_text(
        self,
        content: str,
        base_metadata: dict,
    ) -> list[DocumentData]:
        if not content:
            return []

        document = Document(
            page_content=content,
            metadata=base_metadata,
        )

        chunks = self.__split_document_to_chunks(document)

        documents_data = [
            DocumentData(content=chunk.page_content, metadata=chunk.metadata)
            for chunk in chunks
        ]

        return documents_data

    def _html_to_text(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Convert HTML to Markdown preserving document structure
        # heading_style="ATX" creates # style headings
        # bullets="-" uses - for unordered lists
        page_text = md(str(soup), heading_style="ATX", bullets="-")

        return page_text

    def __split_docs(self, documents, chunk_size: int, chunk_overlap: int = 0):
        # Split documents to chunks
        # First try to split it using CharacterTextSplitter - It uses \n\n only to split and it can fail
        char_text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        splitted_docs_simple = char_text_splitter.split_documents(documents)

        # Now let's split all the documents that did not fit with a recursive splitter
        # It will split the doc using  ["\n\n", "\n", " ", ""]
        recursive_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return recursive_text_splitter.split_documents(splitted_docs_simple)

    def __split_document_to_chunks(self, document: Document) -> list[Document]:
        main_title = document.metadata.get("title")
        document_chunks = self.__split_docs([document], 12000)
        chunks_total = len(document_chunks)

        for i, chunk in enumerate(document_chunks):
            chunk_number = i + 1
            chunk_title = f"{main_title} ({chunk_number}/{chunks_total})"

            chunk.metadata.update(
                {
                    "chunkTitle": chunk_title,
                    "chunkNumber": chunk_number,
                    "chunksTotal": chunks_total,
                },
            )

        return document_chunks

    def __group_documents_by_source_id(self, documents: list[dict]) -> dict:
        grouped_documents = {}

        for document in documents:
            metadata = document.get("metadata", {})
            title = metadata.get("title")
            source_id = metadata.get("sourceId")

            if not source_id:
                continue

            modified_time = metadata.get("modifiedTime")
            document_id = document.get("id")

            if source_id not in grouped_documents:
                grouped_documents[source_id] = {
                    "ids": [document_id],
                    "title": title,
                    "modifiedTime": modified_time,
                }
            else:
                grouped_documents[source_id]["ids"].append(document_id)

        return grouped_documents

    def __get_unchanged_record_ids(
        self,
        records_by_id: dict[str, SourceBasicMetadata],
        grouped_documents_by_record_id: dict,
    ):
        result = set()

        for record_id, record_info in records_by_id.items():
            documents_for_record = grouped_documents_by_record_id.get(record_id)
            if documents_for_record and self.is_record_unchanged(
                record_info,
                documents_for_record,
            ):
                result.add(record_id)

        return result

    def __get_document_ids_for_records(
        self,
        grouped_documents_by_record_id: dict,
        record_ids_set: set[str],
    ) -> list[str]:
        return [
            document_id
            for record_id in record_ids_set
            for document_id in (
                grouped_documents_by_record_id.get(record_id) or {}
            ).get("ids", [])
        ]
