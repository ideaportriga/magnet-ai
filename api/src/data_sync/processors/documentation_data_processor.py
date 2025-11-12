"""Documentation Data Processor

Processes documentation pages from VitePress sites.
"""

import logging
from typing import List

from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sources.vitepress.source import DocumentationPage, VitePressDataSource
from data_sync.data_processor import DataProcessor
from models import DocumentData

logger = logging.getLogger(__name__)


class DocumentationDataProcessor(DataProcessor):
    """Processor for VitePress documentation pages."""

    def __init__(
        self, data_source: VitePressDataSource, collection_config: dict
    ) -> None:
        """Initialize the documentation processor.

        Args:
            data_source: VitePress data source instance
            collection_config: Collection configuration dictionary
        """
        logger.info("Initializing DocumentationDataProcessor")
        self.__data_source = data_source
        self.__collection_config = collection_config
        self.__pages: List[DocumentationPage] = []
        self.__basic_metadata_cache: List[SourceBasicMetadata] = []

    @property
    def data_source(self) -> VitePressDataSource:
        """Get the data source."""
        return self.__data_source

    async def load_data(self) -> None:
        """Load documentation pages from the data source."""
        logger.info("Loading documentation pages")
        try:
            self.__pages = await self.__data_source.get_data()
            logger.info(f"Loaded {len(self.__pages)} documentation pages")

            # Create basic metadata cache
            logger.info("Creating basic metadata cache")
            self.__basic_metadata_cache = self.get_all_records_basic_metadata()
            logger.info(f"Cached metadata for {len(self.__basic_metadata_cache)} pages")
        except Exception as e:
            logger.error(f"Failed to load documentation pages: {e}")
            self.__pages = []
            self.__basic_metadata_cache = []
            raise

    def get_all_records_basic_metadata(self) -> List[SourceBasicMetadata]:
        """Get basic metadata for all documentation pages.

        Returns:
            List of SourceBasicMetadata objects
        """
        if not self.__pages:
            logger.warning("No pages loaded. Call load_data() first.")
            return []

        logger.info("Extracting basic metadata for all pages")
        metadata_list = []

        for page in self.__pages:
            # Use URL as unique identifier
            source_id = page.url
            
            # Modified date is not available for static docs, use empty string
            # This means pages will be re-synced every time, which is acceptable
            # for documentation that might change frequently
            modified_date = ""

            metadata = SourceBasicMetadata(
                title=page.title,
                modified_date=modified_date,
                source_id=source_id,
            )
            metadata_list.append(metadata)

        logger.info(f"Created metadata for {len(metadata_list)} pages")
        return metadata_list

    async def create_chunks_from_doc(self, id: str) -> List[DocumentData]:
        """Create document chunks from a documentation page.

        Args:
            id: Page identifier (URL)

        Returns:
            List of DocumentData objects with content and metadata

        Raises:
            ValueError: If page with given ID is not found
        """
        logger.info(f"Creating chunks for documentation page: {id}")

        # Find the page by ID (URL)
        page = next((p for p in self.__pages if p.url == id), None)

        if not page:
            error_msg = f"Page with ID {id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Processing page: {page.title} ({page.url})")

        # Create base metadata
        base_metadata = {
            "sourceId": page.url,
            "name": page.title,
            "path": page.url,
            "source": page.url,
            "title": page.title,
            "language": page.language,
            "section": page.section,
            "createdTime": "",  # Not available for static docs
            "modifiedTime": "",  # Not available for static docs
        }

        logger.debug(f"Base metadata: {base_metadata}")

        # Use the built-in method to create documents from plain text
        # This will handle chunking according to collection config
        documents = self.create_documents_from_plain_text(
            page.content,
            base_metadata,
        )

        logger.info(f"Created {len(documents)} chunks for page: {page.title}")
        return documents
