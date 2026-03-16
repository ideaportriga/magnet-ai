import logging
import os

import aiofiles
import aiofiles.os
import httpx

from data_sources.data_source import DataSource

logger = logging.getLogger(__name__)


class UrlDataSource(DataSource[str]):
    """Data source for interacting with files via public URLs."""

    def __init__(
        self,
        urls: list[str],
        allowed_extensions: list[str] | None = None,
        local_files: list[dict] | None = None,
    ) -> None:
        """Initializes the UrlDataSource with a list of URLs and optional local files.

        Args:
            urls (List[str]): A list of public URLs pointing to files.
            allowed_extensions (List[str], optional): List of allowed file extensions (e.g., ['.pdf', '.mp4']).
            If None, all files are allowed.
            local_files: Optional list of dicts with 'filename' and 'storage_path' keys
            for files uploaded from the filesystem.

        """
        self._urls = urls
        self._local_files = local_files or []
        self._allowed_extensions = (
            {ext.lower() for ext in allowed_extensions} if allowed_extensions else None
        )

    @property
    def name(self) -> str:
        return "File"

    @property
    def source_description(self) -> str:
        """Provides a description of the data source.

        Returns:
            str: Description of the URL data source.

        """
        return f"URL Data Source with {len(self._urls)} URLs."

    async def get_data(self) -> list[str]:
        """Retrieves the list of URLs and local file identifiers, optionally filtered.

        Returns:
            List[str]: A list of filtered URLs and local:// identifiers.

        """
        urls = self._urls
        if self._allowed_extensions:
            urls = [
                url
                for url in urls
                if self._get_extension(url) in self._allowed_extensions
            ]
            logger.info(
                f"Filtered {len(urls)} URLs based on allowed extensions.",
            )
        else:
            logger.info(f"Returning all {len(urls)} URLs.")

        # Add local file identifiers
        for lf in self._local_files:
            local_id = f"local://{lf['storage_path']}"
            if self._allowed_extensions:
                ext = os.path.splitext(lf["filename"])[1].lower()
                if ext not in self._allowed_extensions:
                    continue
            urls.append(local_id)

        if self._local_files:
            logger.info(f"Added {len(self._local_files)} local files.")

        return urls

    async def download_file(self, url: str, local_path: str) -> None:
        """Downloads a file from a given URL to a local path.

        Args:
            url (str): The URL of the file to download.
            local_path (str): The local filesystem path where the file will be saved.

        Raises:
            RuntimeError: If the download fails.

        """
        logger.info(f"Downloading file from {url} to {local_path}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                dir_path = os.path.dirname(local_path)
                if dir_path:
                    await aiofiles.os.makedirs(dir_path, exist_ok=True)

                async with aiofiles.open(local_path, "wb") as output_file:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        if chunk:
                            await output_file.write(chunk)
            logger.info(f"Successfully downloaded {url} to {local_path}")
        except httpx.RequestError as e:
            logger.error(f"Failed to download file from {url}: {e}")
            raise RuntimeError(f"Failed to download file from {url}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while downloading file from {url}: {e}")
            raise RuntimeError(
                f"Unexpected error while downloading file from {url}: {e}"
            ) from e

    def _get_extension(self, url: str) -> str:
        """Extracts the file extension from a URL.

        Args:
            url (str): The URL of the file.

        Returns:
            str: The file extension (e.g., '.pdf').

        """
        return os.path.splitext(url.split("?")[0])[1].lower()
