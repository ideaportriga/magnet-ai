from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_abstract import SharePointAbstractDataSource
from data_sources.sharepoint.types import SharePointFileExtension, SharePointRootFolder


class SharePointPagesDataSource(SharePointAbstractDataSource):
    def __init__(self, ctx: ClientContext, page_name: str | None = None) -> None:
        super().__init__(ctx)
        self.__page_name = page_name

    @property
    def name(self) -> str:
        return "Sharepoint Pages"

    async def _get_syncable_files(self) -> list[File]:
        pages = await self._aget_folder_files(
            folder_name=SharePointRootFolder.PAGES.value,
            filter=self.__page_name,
            file_extensions=[SharePointFileExtension.PAGE],
        )

        return pages
