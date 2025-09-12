import os
from abc import abstractmethod
from logging import getLogger
from urllib.parse import quote, urlparse

from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_abstract import SharePointAbstractDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.processors.sharepoint.sharepoint_site_page_processor import (
    SharepointSitePageProcessor,
)
from models import DocumentData
from utils.datetime_utils import utc_to_isoformat

logger = getLogger(__name__)


class SharepointAbstractDataProcessor(DataProcessor, SharepointSitePageProcessor):
    _data_source: SharePointAbstractDataSource
    __files: list[File]

    def __init__(self, data_source: SharePointAbstractDataSource) -> None:
        self._data_source = data_source

    @property
    def data_source(self) -> SharePointAbstractDataSource:
        return self._data_source

    async def load_data(self) -> None:
        self.__files = await self._data_source.get_data()

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        return [
            SourceBasicMetadata(
                file.name or "",
                utc_to_isoformat(file.time_last_modified)
                if file.time_last_modified
                else "",
                file.unique_id or "",
            )
            for file in self.__files
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        file = next((file for file in self.__files if file.unique_id == id), None)

        if not file:
            raise Exception(f"File with id {id} not found")

        return await self._process_file(file)

    @abstractmethod
    async def _process_file(self, file: File) -> list[DocumentData]: ...

    def _create_base_metadata(self, file: File) -> dict:
        file_name = file.name or ""
        file_unique_id = file.unique_id or ""
        file_path = file.serverRelativeUrl or ""
        base_path = self._get_base_path(file.context.base_url)
        file_source = f"{base_path}{quote(file_path)}"
        file_title = file.properties.get("Title") or os.path.splitext(file_name)[0]
        created_time = utc_to_isoformat(file.time_created) if file.time_created else ""
        modified_time = (
            utc_to_isoformat(file.time_last_modified) if file.time_last_modified else ""
        )

        return dict(
            {
                "sourceId": file_unique_id,
                "name": file_name,
                "path": file_path,
                "source": file_source,
                "title": file_title,
                "createdTime": created_time,
                "modifiedTime": modified_time,
            },
        )

    def _get_base_path(self, url: str) -> str:
        parsed_url = urlparse(url)
        base_path = parsed_url.scheme + "://" + parsed_url.netloc
        return base_path
