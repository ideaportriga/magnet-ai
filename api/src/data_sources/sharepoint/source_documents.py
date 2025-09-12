from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_abstract import SharePointAbstractDataSource
from data_sources.sharepoint.types import SharePointFileExtension, SharePointRootFolder


class SharePointDocumentsDataSource(SharePointAbstractDataSource):
    def __init__(
        self,
        ctx: ClientContext,
        folder: str | None = None,
        recursive: bool = False,
    ) -> None:
        super().__init__(ctx)
        self.folder = folder
        self.recursive = recursive

    @property
    def name(self) -> str:
        return "Sharepoint Documents"

    async def _get_syncable_files(self) -> list[File]:
        folder_name = SharePointRootFolder.DOCUMENTS.value

        if self.folder:
            folder_name += f"/{self.folder}"

        documents = await self._aget_folder_files(
            folder_name=folder_name,
            recursive=self.recursive,
            file_extensions=[SharePointFileExtension.PDF, SharePointFileExtension.MP4],
        )

        return documents
