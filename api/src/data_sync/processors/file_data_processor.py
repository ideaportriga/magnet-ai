from __future__ import annotations

import logging  # Logging has been uncommented as per requirement
import os
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from uuid import UUID

import aiofiles
import httpx

if TYPE_CHECKING:
    from storage import StorageService

    from sqlalchemy.ext.asyncio import AsyncSession
from kreuzberg import ExtractionConfig, PageConfig, extract_bytes
from langchain.schema import Document
from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from data_sources.file.source import UrlDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.models import ChunkingStrategy
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

DEFAULT_CHUNK_SIZE = 12000
DEFAULT_CHUNK_OVERLAP = 2000


class UrlDataProcessor(DataProcessor):
    """Class for processing data from a list of URLs."""

    __data_source: UrlDataSource
    __collection_config: dict
    __urls: list[str]
    __basic_metadata_cache: list[SourceBasicMetadata]

    def __init__(
        self,
        data_source: UrlDataSource,
        collection_config: dict,
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        """Initializes UrlDataProcessor with a UrlDataSource data source.

        Args:
            data_source: Data source with public URLs.
            storage_service: Optional StorageService for reading stored:// files.
            db_session: Optional DB session for StorageService queries.

        """
        logger.info("Initializing UrlDataProcessor with provided data source.")
        self.__data_source = data_source
        self.__collection_config = collection_config
        self.__basic_metadata_cache = []
        self._storage_service = storage_service
        self._db_session = db_session

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
            is_stored = entry.startswith("stored://")

            if is_stored:
                file_id = entry[len("stored://") :]
                stored_file = await self._get_stored_file(file_id)
                file_name = stored_file.filename if stored_file else file_id
                last_modified = (
                    stored_file.created_at.isoformat()
                    if stored_file and stored_file.created_at
                    else ""
                )
            elif is_local:
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
        is_stored = id.startswith("stored://")

        if is_stored:
            file_id = id[len("stored://") :]
            stored_file = await self._get_stored_file(file_id)
            if not stored_file:
                raise Exception(f"Stored file {file_id} not found")
            file_name = stored_file.filename
        elif is_local:
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
        if is_stored:
            logger.info(f"Reading stored file: {file_id}")
            try:
                file_bytes = await self._storage_service.get_file_content(stored_file)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Stored file '{file_name}' (id={file_id}) is missing from backend "
                    f"'{stored_file.backend_key}' at path '{stored_file.path}'. "
                    "The file may have been deleted or the storage was cleared."
                )
            logger.info(f"Read {len(file_bytes)} bytes from stored file: {file_name}")
        elif is_local:
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
        file_title = os.path.splitext(file_name)[0]

        if url.startswith(("local://", "stored://")):
            modified_time = ""
        else:
            modified_time = await self.__get_last_modified(url)
        created_time = modified_time

        # For stored files, provide a browser-accessible download URL
        # instead of the internal stored:// protocol for sourceId/path/source.
        if url.startswith("stored://"):
            file_id = url[len("stored://") :]
            download_url = f"/api/admin/files/{file_id}/download"
        else:
            download_url = url

        metadata = {
            "sourceId": download_url,
            "name": file_title,
            "path": download_url,
            "source": download_url,
            "title": file_title,
            "createdTime": created_time,
            "modifiedTime": modified_time,
        }

        logger.debug(f"Base metadata created: {metadata}")
        return metadata

    async def _get_stored_file(self, file_id: str):  # noqa: ANN201
        """Fetch a StoredFile by its UUID string."""
        if not self._storage_service or not self._db_session:
            raise RuntimeError(
                "StorageService and db_session are required for stored:// files"
            )
        return await self._storage_service.get(self._db_session, UUID(file_id))

    def __get_file_name(self, url: str) -> str:
        """Extracts the file name from the URL.

        Args:
            url (str): Public URL of the file.

        Returns:
            str: File name.

        """
        logger.debug(f"Extracting file name from URL: {url}")
        parsed = urlparse(url)
        file_name = os.path.basename(parsed.path)
        if not file_name:
            file_name = parsed.hostname or ""
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
        if result.pages and len(result.pages) > 1:
            for i, page in enumerate(result.pages):
                page_num = i + 1  # PDF pages are 1-indexed
                page_meta = {**base_metadata, "page": i}
                # Append #page=N so browser opens PDF at the right page
                if base_metadata.get("source", "").startswith("/api/"):
                    page_meta["source"] = f"{base_metadata['source']}#page={page_num}"
                page_documents.append(
                    Document(
                        page_content=clean_text(page["content"]),
                        metadata=page_meta,
                    )
                )
        else:
            # Single page or no pages (e.g. Word files) — don't set page metadata
            content = result.pages[0]["content"] if result.pages else result.content
            page_documents.append(
                Document(
                    page_content=clean_text(content),
                    metadata=base_metadata,
                )
            )

        # Apply chunking strategy from collection config
        chunking_config = self.__collection_config.get("chunking", {})
        strategy = chunking_config.get("strategy")

        if strategy == ChunkingStrategy.RECURSIVE_CHARACTER_TEXT_SPLITTING:
            chunk_size = self.__parse_int(
                chunking_config.get("chunk_size"), DEFAULT_CHUNK_SIZE
            )
            chunk_overlap = self.__parse_int(
                chunking_config.get("chunk_overlap"), DEFAULT_CHUNK_OVERLAP
            )
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            page_documents = [
                Document(
                    page_content=clean_text(chunk.page_content),
                    metadata=chunk.metadata,
                )
                for chunk in splitter.split_documents(page_documents)
            ]
            logger.info(
                f"Applied recursive chunking (size={chunk_size}, overlap={chunk_overlap}): "
                f"{len(page_documents)} chunks from {file_name}."
            )
        elif strategy == ChunkingStrategy.HTML_HEADER_SPLITTING:
            full_content = "\n\n".join(doc.page_content for doc in page_documents)
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
            raw_chunks = splitter.split_text(full_content)
            page_documents = self.__process_html_header_chunks(
                raw_chunks, base_metadata
            )
            logger.info(
                f"Applied HTML header splitting: "
                f"{len(page_documents)} chunks from {file_name}."
            )
        else:
            logger.info(
                f"No chunking applied (strategy={strategy}): "
                f"{len(page_documents)} chunks from {file_name}."
            )

        return page_documents

    @staticmethod
    def __parse_int(value, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def __process_html_header_chunks(
        chunks: list[Document], base_metadata: dict
    ) -> list[Document]:
        processed: list[Document] = []
        for chunk in chunks:
            headers = {
                key: chunk.metadata.pop(key, None)
                for key in [
                    "Header 1",
                    "Header 2",
                    "Header 3",
                    "Header 4",
                    "Header 5",
                    "Header 6",
                ]
            }
            # Skip chunks that are just a header
            if chunk.page_content in [v for v in headers.values() if v]:
                continue
            content = ""
            for level, (_, header) in enumerate(headers.items(), 1):
                if header:
                    content += f"{'#' * level} {header}\n"
            content += chunk.page_content
            processed.append(
                Document(
                    page_content=clean_text(content),
                    metadata=base_metadata,
                )
            )
        return processed
