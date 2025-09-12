from logging import getLogger

from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_pages import SharePointPagesDataSource
from data_sync.processors.sharepoint.sharepoint_abstract_data_processor import (
    SharepointAbstractDataProcessor,
)
from data_sync.utils import clean_text
from models import DocumentData

logger = getLogger(__name__)


class SharepointPagesDataProcessor(SharepointAbstractDataProcessor):
    def __init__(
        self,
        data_source: SharePointPagesDataSource,
        embed_title: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.__embed_title = embed_title

    async def _process_file(self, file: File) -> list[DocumentData]:
        sharepoint_url = self._data_source.sharepoint_url
        file_name = file.name
        if not file_name:
            logger.warning("Cannot define file type as file name is empty")
            return []

        document_data_to_add: list[DocumentData] = []

        base_metadata = self._create_base_metadata(file=file)

        if file_name.endswith(".aspx"):
            base_url = self._get_base_path(sharepoint_url)
            embed_title = self.__embed_title

            documents = self._create_site_page_documents(
                base_metadata=base_metadata,
                file=file,
                base_url=base_url,
                embed_title=embed_title,
            )

            document_data_to_add.extend(
                [
                    DocumentData(
                        content=clean_text(doc.page_content), metadata=doc.metadata
                    )
                    for doc in documents
                ],
            )

        return document_data_to_add
