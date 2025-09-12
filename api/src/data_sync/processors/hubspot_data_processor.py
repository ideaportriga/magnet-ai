from typing import Any

from data_sources.hubspot.source import HubspotDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from models import DocumentData


class HubspotDataProcessor(DataProcessor):
    """Class for processing data from HubSpot."""

    __data_source: HubspotDataSource
    __records: list[dict[str, Any]]

    def __init__(self, data_source: HubspotDataSource) -> None:
        """Initializes HubspotDataProcessor with a HubSpot data source.

        Args:
            data_source (HubspotDataSource): Data source containing information from HubSpot.

        """
        self.__data_source = data_source
        self.__records = []

    @property
    def data_source(self) -> HubspotDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        """Loads data from the data source and stores it in self.__records."""
        self.__records = await self.__data_source.get_data()

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        """Extracts basic metadata for all records.

        Returns:
            List[SourceBasicMetadata]: List of basic metadata for each record.

        """
        basic_metadata_list = []
        for record in self.__records:
            title = record.get("title", "Untitled")
            unique_id = str(record.get("id", ""))
            published_date_iso = record.get("publishedDate", "")

            metadata = SourceBasicMetadata(
                title=title,
                modified_date=published_date_iso,
                source_id=unique_id,
            )
            basic_metadata_list.append(metadata)

        return basic_metadata_list

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        """Creates documents for the given identifier.

        Args:
            id (str): Unique record identifier.

        Returns:
            List[DocumentData]: List of documents with content and metadata.

        """
        # Filter records by the given IDs
        record = next(
            (record for record in self.__records if str(record.get("id", "")) == id),
            None,
        )

        if not record:
            raise Exception(f"Record with id {id} not found")

        record_id = str(record.get("id", ""))
        record_type = record.get("type", "")
        url = record.get("url", "")
        title = record.get("title", "Untitled")
        description = record.get("description", "")
        category = record.get("category", "Unknown Category")
        language = record.get("language", "en")
        domain = record.get("domain", "")
        published_date_iso = record.get("publishedDate", "")
        content = record.get("content", "")

        if not content:
            raise Exception(f"Record with id {id} has no content")

        metadata = {
            "sourceId": record_id,
            "title": title,
            "description": description,
            "source": url,
            "category": category,
            "language": language,
            "domain": domain,
            "modifiedTime": published_date_iso,
            "createdTime": published_date_iso,  # Assuming 'createdDate' is same as 'publishedDate'
            "type": record_type,
        }

        document_data = DocumentData(content=content, metadata=metadata)
        return [document_data]
