import logging  # Logging has been uncommented as per requirement
import os
from urllib.parse import urlparse

import aiofiles
import httpx
from kreuzberg import ExtractionConfig, PageConfig, extract_bytes
from langchain.schema import Document

from data_sources.file.source import UrlDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.utils import clean_text
from models import DocumentData
from services.knowledge_graph.readers.kreuzberg_reader import mime_type_from_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class UrlDataProcessor(DataProcessor):
    """Class for processing data from a list of URLs."""

    __data_source: UrlDataSource
    __collection_config: dict
    __urls: list[str]
    __basic_metadata_cache: list[SourceBasicMetadata]

    def __init__(self, data_source: UrlDataSource, collection_config: dict) -> None:
        """Initializes UrlDataProcessor with a UrlDataSource data source.

        Args:
            data_source (UrlDataSource): Data source with public URLs.

        """
        logger.info("Initializing UrlDataProcessor with provided data source.")
        self.__data_source = data_source
        self.__collection_config = collection_config
        self.__basic_metadata_cache = []

    async def load_data(self) -> None:
        """Loads data from the data source and stores it in self.__urls."""
        logger.info("Loading data from the data source.")
        try:
            self.__urls = await self.data_source.get_data()
            logger.info(f"Loaded {len(self.__urls)} URLs from the data source.")

            logger.info("Loading basic metadata for all URLs.")
            self.__basic_metadata_cache = (
                await self.get_all_records_basic_metadata_async()
            )
            logger.info(
                f"Cached metadata for {len(self.__basic_metadata_cache)} records."
            )
        except Exception as e:
            logger.error(f"Failed to load data from the data source: {e}")
            self.__urls = []
            self.__basic_metadata_cache = []

    @property
    def data_source(self) -> UrlDataSource:
        return self.__data_source

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        if not self.__basic_metadata_cache:
            logger.warning(
                "Basic metadata cache is empty. Make sure load_data() was called first."
            )
        return self.__basic_metadata_cache

    async def get_all_records_basic_metadata_async(self) -> list[SourceBasicMetadata]:
        """Extracts basic metadata for all entries (URLs and local files).

        Returns:
            List[SourceBasicMetadata]: List of basic metadata for each entry.

        """
        logger.info("Extracting basic metadata for all entries.")
        basic_metadata_list = []
        for entry in self.__urls:
            logger.debug(f"Processing entry: {entry}")
            is_local = entry.startswith("local://")

            if is_local:
                storage_path = entry[len("local://") :]
                file_name = os.path.basename(storage_path)
                last_modified = ""
            else:
                file_name = self.__get_file_name(entry)
                last_modified = await self.__get_last_modified(entry)

            unique_id = entry
            title = os.path.splitext(file_name)[0] if file_name else "Untitled"
            metadata = SourceBasicMetadata(
                title=title,
                modified_date=last_modified,
                source_id=unique_id,
            )
            basic_metadata_list.append(metadata)
            logger.debug(f"Extracted metadata: {metadata}")

        logger.info(f"Extracted metadata for {len(basic_metadata_list)} records.")
        return basic_metadata_list

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        """Creates documents for the given identifier (URL or local:// path).

        Args:
            id (str): Unique identifier (URL or local:// path).

        Returns:
            List[DocumentData]: List of documents with metadata.

        """
        logger.info(f"Creating documents for {id}.")

        # Check if the identifier exists in our data
        entry = next((e for e in self.__urls if e == id), None)
        if not entry:
            raise Exception(f"Entry with id {id} not found")

        is_local = id.startswith("local://")

        if is_local:
            storage_path = id[len("local://") :]
            file_name = os.path.basename(storage_path)
        else:
            file_name = self.__get_file_name(id)

        if not file_name:
            raise Exception(f"Could not extract file name from: {id}")

        logger.info(f"Processing: {id} (file: {file_name})")
        base_metadata = await self.__create_base_metadata(url=id, file_name=file_name)
        logger.debug(f"Base metadata created: {base_metadata}")

        # Download or read file bytes
        if is_local:
            logger.info(f"Reading local file: {storage_path}")
            async with aiofiles.open(storage_path, "rb") as f:
                file_bytes = await f.read()
            logger.info(f"Read {len(file_bytes)} bytes from local file: {file_name}")
        else:
            logger.info(f"Downloading file from URL: {id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(id, follow_redirects=True, timeout=60.0)
                response.raise_for_status()
                file_bytes = response.content
            logger.info(f"Downloaded {len(file_bytes)} bytes from URL: {file_name}")

        documents = await self.__create_documents_from_bytes(
            base_metadata=base_metadata,
            file_bytes=file_bytes,
            file_name=file_name,
        )
        logger.info(
            f"Created {len(documents)} document chunks from: {file_name}",
        )

        return [
            DocumentData(content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        ]

    async def __create_base_metadata(self, url: str, file_name: str) -> dict:
        """Creates base metadata for a document based on the URL or local path.

        Args:
            url (str): Public URL or local:// identifier.
            file_name (str): Name of the file.

        Returns:
            dict: Base metadata.

        """
        logger.debug(f"Creating base metadata for: {url}")
        file_unique_id = url
        file_path = url
        file_title = os.path.splitext(file_name)[0]

        if url.startswith("local://"):
            modified_time = ""
        else:
            modified_time = await self.__get_last_modified(url)
        created_time = modified_time

        metadata = {
            "sourceId": file_unique_id,
            "name": file_title,
            "path": file_path,
            "source": file_path,
            "title": file_title,
            "createdTime": created_time,
            "modifiedTime": modified_time,
        }

        logger.debug(f"Base metadata created: {metadata}")
        return metadata

    def __get_file_name(self, url: str) -> str:
        """Extracts the file name from the URL.

        Args:
            url (str): Public URL of the file.

        Returns:
            str: File name.

        """
        logger.debug(f"Extracting file name from URL: {url}")
        path = urlparse(url).path
        file_name = os.path.basename(path)
        logger.debug(f"Extracted file name: {file_name}")
        return file_name

    async def __get_last_modified(self, url: str) -> str:
        """Retrieves the last modified date of the file via HTTP header.

        Args:
            url (str): Public URL of the file.

        Returns:
            str: Last modified date in ISO format, or empty string if unavailable.

        """
        logger.debug(f"Retrieving last modified date for URL: {url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()
                last_modified = response.headers.get("Last-Modified")
                if last_modified:
                    from email.utils import parsedate_to_datetime

                    dt = parsedate_to_datetime(last_modified)
                    iso_date = dt.isoformat()
                    logger.debug(f"Last modified date for URL {url}: {iso_date}")
                    return iso_date
                logger.warning(f"No 'Last-Modified' header found for URL: {url}")
        except httpx.RequestError as e:
            logger.error(f"Error retrieving last modified date for URL {url}: {e}")
        return ""

    async def __create_documents_from_bytes(
        self,
        base_metadata: dict,
        file_bytes: bytes,
        file_name: str,
    ):
        """Creates documents from file bytes using kreuzberg (format-agnostic).

        Args:
            base_metadata (dict): Base metadata.
            file_bytes (bytes): Raw file content.
            file_name (str): Original filename (used for MIME detection).

        Returns:
            List[Document]: List of documents.

        """
        logger.info(f"Creating documents for file: {file_name}")

        mime_type = mime_type_from_filename(file_name)
        if not mime_type:
            from kreuzberg import detect_mime_type

            mime_type = detect_mime_type(file_bytes)
        logger.info(f"Resolved MIME type: {mime_type} for {file_name}")

        config = ExtractionConfig(
            output_format="markdown",
            pages=PageConfig(extract_pages=True),
        )
        result = await extract_bytes(file_bytes, mime_type, config=config)

        # Build per-page documents (if pages are available)
        page_documents: list[Document] = []
        if result.pages:
            for i, page in enumerate(result.pages):
                page_documents.append(
                    Document(
                        page_content=clean_text(page["content"]),
                        metadata={**base_metadata, "page": i},
                    )
                )
        else:
            page_documents.append(
                Document(
                    page_content=clean_text(result.content),
                    metadata=base_metadata,
                )
            )

        logger.info(f"Extracted {len(page_documents)} chunks from {file_name}.")
        return page_documents
