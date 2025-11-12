"""Confluence Data Processor

This processor handles the transformation of Confluence pages into document chunks.
"""

from data_sources.confluence.source import ConfluenceDataSource
from data_sources.confluence.types import ConfluencePage
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from models import DocumentData


class ConfluenceDataProcessor(DataProcessor):
    """Data processor for Confluence pages"""

    __data_source: ConfluenceDataSource
    __all_pages: list[ConfluencePage]

    def __init__(self, data_source: ConfluenceDataSource) -> None:
        self.__data_source = data_source

    @property
    def data_source(self) -> ConfluenceDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        try:
            self.__all_pages = await self.data_source.get_data()
        except Exception as e:
            # Handle or log the exception as needed
            raise e

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        return [
            SourceBasicMetadata(page.title, page.version.when, page.id)
            for page in self.__all_pages
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        page = next((page for page in self.__all_pages if page.id == id), None)

        if not page:
            raise Exception(f"Page with id {id} not found")

        return [
            document
            for document in self.create_documents_from_html(
                page.body.storage.value,
                self.__create_base_metadata(page),
            )
        ]

    def is_record_unchanged(
        self,
        record_basic_metadata: SourceBasicMetadata,
        document: dict,
    ) -> bool:
        return record_basic_metadata.title == document.get(
            "title",
        ) and super().is_record_unchanged(record_basic_metadata, document)

    def __create_base_metadata(self, page: ConfluencePage) -> dict:
        page_source = f"{self.__data_source.instance_url}{page.links.webui}"

        return {
            "sourceId": page.id,
            "name": page.title,
            "source": page_source,
            "title": page.title,
            "createdTime": page.history.created_date,
            "modifiedTime": page.version.when,
        }
