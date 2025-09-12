import logging  # Logging has been uncommented as per requirement
import os
from urllib.parse import urlparse

import httpx
from langchain.schema import Document

from data_sources.file.source import UrlDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.splitters.pdf_splitter import PdfSplitter
from models import DocumentData

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
        """Extracts basic metadata for all URLs.

        Returns:
            List[SourceBasicMetadata]: List of basic metadata for each URL.

        """
        logger.info("Extracting basic metadata for all URLs.")
        basic_metadata_list = []
        for url in self.__urls:
            logger.debug(f"Processing URL: {url}")
            file_name = self.__get_file_name(url)
            unique_id = url  # Use URL as unique identifier
            last_modified = await self.__get_last_modified(url)
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
        """Creates documents for the given identifier (URLs).

        Args:
            id (str): Unique identifier (URL).

        Returns:
            List[DocumentData]: List of documents with metadata.

        """
        logger.info(f"Creating documents for {id}.")
        docs_to_add: list[Document] = []

        # Filter URLs by given IDs
        url = next((url for url in self.__urls if url == id), None)

        if not url:
            raise Exception(f"URL with id {id} not found")

        logger.info(f"Processing URL: {url}")
        file_name = self.__get_file_name(url)

        if not file_name:
            raise Exception(f"Could not extract file name from URL: {url}")

        base_metadata = await self.__create_base_metadata(url=url, file_name=file_name)
        logger.debug(f"Base metadata created: {base_metadata}")

        if file_name.lower().endswith(".pdf"):
            local_directory = os.environ.get("LOCAL_DIRECTORY") or "./files"
            logger.info(f"Detected PDF file. Processing PDF: {file_name}")
            documents = await self.__create_pdf_documents(
                base_metadata=base_metadata,
                url=url,
                local_directory=local_directory,
            )
            logger.info(
                f"Created {len(documents)} document chunks from PDF: {file_name}",
            )
            docs_to_add.extend(documents)
        else:
            logger.info(f"Non-PDF file detected ({file_name}). Skipping processing.")

        return [
            DocumentData(content=doc.page_content, metadata=doc.metadata)
            for doc in docs_to_add
        ]

    async def __create_base_metadata(self, url: str, file_name: str) -> dict:
        """Creates base metadata for a document based on the URL.

        Args:
            url (str): Public URL of the file.
            file_name (str): Name of the file.

        Returns:
            dict: Base metadata.

        """
        logger.debug(f"Creating base metadata for URL: {url}")
        file_unique_id = url  # Use URL as unique identifier
        file_path = url  # Full URL as path
        file_title = os.path.splitext(file_name)[0]
        modified_time = await self.__get_last_modified(url)
        created_time = modified_time  # No creation time data

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

    # region PDF processing
    async def __create_pdf_documents(
        self,
        base_metadata: dict,
        url: str,
        local_directory: str,
    ):
        """Creates documents for a PDF file.

        Args:
            base_metadata (dict): Base metadata.
            url (str): Public URL of the PDF file.
            local_directory (str): Local directory for temporary PDF storage.

        Returns:
            List[Document]: List of documents.

        """
        file_name = base_metadata.get("name", "unknown.pdf")
        logger.info(f"Creating PDF documents for file: {file_name}")

        local_path = os.path.join(local_directory, file_name)
        logger.debug(f"Local path for PDF download: {local_path}")

        logger.info(f"Downloading PDF from URL: {url} to {local_path}")
        await self.__data_source.download_file(url, local_path)
        logger.info(f"Successfully downloaded PDF: {file_name}")

        logger.info(f"Loading and splitting PDF: {file_name}")
        chunks = await PdfSplitter(
            local_path,
            base_metadata,
            chunking_config=self.__collection_config.get("chunking"),
        ).split()
        os.remove(local_path)

        chunks_total = len(chunks)
        logger.info(f"Split PDF into {chunks_total} chunks.")

        return chunks
