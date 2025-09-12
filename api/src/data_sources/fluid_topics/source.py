import logging
import os
import traceback

import aiofiles
import httpx

from data_sources.data_source import DataSource
from data_sources.fluid_topics.types import FluidTopicsDocument

logger = logging.getLogger(__name__)


class FluidTopicsDataSource(DataSource[str]):
    """Data source for interacting with Fluid Topics API."""

    def __init__(self, filters: list[dict]) -> None:
        """Initializes the FluidTopicsDataSource with a list of filters.

        Args:
            filters (List[dict]): A list of filters for the Fluid Topics.

        """
        self._search_api_key = os.getenv("FLUID_TOPICS_API_KEY")
        self._search_api_url = os.getenv("FLUID_TOPICS_SEARCH_API_URL")
        self._pdf_api_url = os.getenv("FLUID_TOPICS_PDF_API_URL")
        self._filters = filters

    @property
    def name(self) -> str:
        return "Fluid Topics"

    @property
    def source_description(self) -> str:
        """Provides a description of the data source.

        Returns:
            str: Description of the Fluid Topics data source.

        """
        return f"Fluid Topics Data Source with {len(self._filters)} filters."

    async def get_data(self) -> list[FluidTopicsDocument]:
        """Retrieves the list of document URLs from Fluid Topics.

        Returns:
            List[str]: A list of document URLs.

        """
        if (
            not self._search_api_key
            or not self._search_api_url
            or not self._pdf_api_url
        ):
            raise RuntimeError(
                "FLUID_TOPICS_SEARCH_API_KEY, FLUID_TOPICS_SEARCH_API_URL or FLUID_TOPICS_PDF_API_URL is not set",
            )

        try:
            documents: list[FluidTopicsDocument] = []
            page = 1
            async with httpx.AsyncClient() as client:
                while True:
                    response = await client.post(
                        self._search_api_url,
                        json={
                            "filters": self._filters,
                            "paging": {
                                "page": page,
                                "perPage": 50,
                            },
                        },
                        headers={"x-api-key": self._search_api_key},
                    )
                    response.raise_for_status()
                    json_response = response.json()
                    for result in json_response.get("results", []):
                        for entry in result.get("entries", []):
                            if entry.get("type") == "DOCUMENT" and entry.get(
                                "document"
                            ):
                                id = entry["document"].get("documentId")
                                file_name = entry["document"].get("filename")
                                title = entry["document"].get("title")
                                mime_type = entry["document"].get("mimeType")
                                # Look for created_date in metadata
                                created_date = None
                                for metadata_item in entry["document"].get(
                                    "metadata", []
                                ):
                                    if metadata_item.get("key") == "created_date":
                                        created_date = (
                                            metadata_item.get("values", [])[0]
                                            if metadata_item.get("values")
                                            else None
                                        )
                                        break
                                modified_date = entry["document"].get(
                                    "lastPublicationDate"
                                )
                                viewer_url = entry["document"].get("viewerUrl")
                                documents.append(
                                    FluidTopicsDocument(
                                        id,
                                        file_name,
                                        title,
                                        mime_type,
                                        created_date,
                                        modified_date,
                                        "",
                                        viewer_url,
                                    ),
                                )
                    if json_response.get("paging", {}).get("isLastPage"):
                        break
                    page += 1
            return documents
        except httpx.RequestError as e:
            logger.error(f"Failed to get data from Fluid Topics: {e}")
            raise RuntimeError(f"Failed to get data from Fluid Topics: {e}") from e

    async def get_url(self, file_name: str) -> str:
        if not self._pdf_api_url or not self._search_api_key:
            raise RuntimeError(
                "FLUID_TOPICS_PDF_API_URL or FLUID_TOPICS_SEARCH_API_KEY is not set",
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._pdf_api_url,
                    params={"fileName": file_name},
                    headers={"x-api-key": self._search_api_key},
                    timeout=httpx.Timeout(20.0, connect=20.0),
                )
                response.raise_for_status()
                return response.text
        except httpx.RequestError:
            logger.error(f"Failed to get URL for {file_name}")
            traceback.print_exc()
            raise

    async def download_file(self, url: str, local_path: str) -> None:
        """Downloads a file from a given URL to a local path.

        Args:
            url (str): The URL of the file to download.
            local_path (str): The local filesystem path where the file will be saved.

        Raises:
            RuntimeError: If the download fails.

        """
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET", url, timeout=httpx.Timeout(20.0, connect=20.0)
                ) as response:
                    response.raise_for_status()
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    async with aiofiles.open(local_path, "wb") as output_file:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            if chunk:
                                await output_file.write(chunk)
        except httpx.RequestError:
            logger.error(f"Failed to download file from {url}")
            traceback.print_exc()
            raise
