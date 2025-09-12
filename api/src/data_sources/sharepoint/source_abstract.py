import asyncio
import os
from abc import ABC, abstractmethod
from typing import cast

import aiofiles
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File, Folder

from data_sources.data_source import DataSource
from data_sources.sharepoint.types import SharePointFileExtension


class SharePointAbstractDataSource(DataSource[File], ABC):
    def __init__(self, ctx: ClientContext) -> None:
        self.__client = ctx

    @property
    def name(self) -> str:
        return "Sharepoint"

    @property
    def sharepoint_url(self) -> str:
        return self.__client.base_url

    async def get_data(self) -> list[File]:
        files = await self._get_syncable_files()

        return files

    async def download_file(self, file: File, local_path: str) -> None:
        async with aiofiles.open(local_path, "wb") as output_file:
            # For some reason, file.download method is not working, so we need to use the get_content method
            # When file.download was called in the multithreaded context, it always returned an empty file
            # file.download(output_file).execute_query()

            file_content = await asyncio.to_thread(
                lambda: file.get_content().execute_query()
            )

            await output_file.write(file_content.value)  # type: ignore

    @abstractmethod
    async def _get_syncable_files(self) -> list[File]: ...

    async def _aget_folder_files(
        self,
        folder_name: str,
        filter: str | None = None,
        file_extensions: list[SharePointFileExtension] = [],
        recursive: bool = False,
    ):
        return await asyncio.to_thread(
            lambda: self._get_folder_files(
                folder_name, filter, file_extensions, recursive
            )
        )

    def _get_folder_files(
        self,
        folder_name: str,
        filter: str | None = None,
        file_extensions: list[SharePointFileExtension] = [],
        recursive: bool = False,
    ) -> list[File]:
        folder = self.__client.web.get_folder_by_server_relative_url(folder_name)

        files: list[File] = []

        if recursive:
            # Recursively process all subfolders
            def process_folder(current_folder: Folder):
                # Get files and folders from current folder
                current_folder.expand(["Files", "Folders"]).get().execute_query_retry()

                # Add files from current folder
                if current_folder.files and len(current_folder.files) > 0:
                    files.extend(cast(list[File], current_folder.files))

                # Process subfolders recursively
                if current_folder.folders:
                    for subfolder in current_folder.folders:
                        process_folder(subfolder)

            process_folder(folder)
        else:
            # For non-recursive search, just get files from current folder
            folder.expand(["Files"]).get().execute_query_retry()
            if folder.files and len(folder.files) > 0:
                files.extend(cast(list[File], folder.files))

        file_extensions_set = frozenset({ext.value for ext in file_extensions})

        files = [
            file
            for file in files
            if (
                (
                    (
                        len(file_extensions_set) > 0
                        and os.path.splitext(file.name or "")[1] in file_extensions_set
                    )
                    or len(file_extensions_set) == 0
                )
                and (
                    (
                        filter
                        and (
                            filter == file.name
                            or filter == os.path.splitext(file.name or "")[0]
                        )
                    )
                    or not filter
                )
            )
        ]

        return files
