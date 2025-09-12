import html
import os
from logging import getLogger

from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_abstract import SharePointAbstractDataSource
from data_sync.processors.sharepoint.sharepoint_abstract_data_processor import (
    SharepointAbstractDataProcessor,
)
from data_sync.splitters.pdf_splitter import PdfSplitter
from data_sync.splitters.video_text_splitter import VideoTextSplitter
from models import DocumentData

logger = getLogger(__name__)


class SharepointDocumentsDataProcessor(SharepointAbstractDataProcessor):
    __collection_config: dict

    def __init__(
        self,
        data_source: SharePointAbstractDataSource,
        collection_config: dict,
    ) -> None:
        super().__init__(data_source)
        self.__collection_config = collection_config

    async def _process_file(self, file: File) -> list[DocumentData]:
        sharepoint_url = self._data_source.sharepoint_url
        file_name = file.name
        if not file_name:
            logger.warning("Cannot define file type as file name is empty")
            return []

        document_data_to_add: list[DocumentData] = []

        base_metadata = self._create_base_metadata(file=file)

        if file_name.endswith(".mp4"):
            documents = await self.__create_video_documents(
                sharepoint_url,
                file,
                base_metadata,
            )
            document_data_to_add.extend(
                [
                    DocumentData(content=doc.page_content, metadata=doc.metadata)
                    for doc in documents
                ],
            )

        elif file_name.endswith(".pdf"):
            documents = await self.__create_pdf_documents(file, base_metadata)
            document_data_to_add.extend(
                [
                    DocumentData(content=doc.page_content, metadata=doc.metadata)
                    for doc in documents
                ],
            )

        return document_data_to_add

    async def __get_video_description(self, file) -> str | None:
        list_item = (
            file.listItemAllFields.select(["VideoDescription"]).get().execute_query()
        )
        video_description = list_item.properties.get("VideoDescription")
        if not video_description:
            return None

        return html.unescape(video_description)

    async def __create_video_documents(
        self,
        sharepoint_url: str,
        file: File,
        base_metadata: dict,
    ):
        logger.info("Sync video `%s`", file.name)

        video_description = await self.__get_video_description(file)

        if not video_description:
            logger.info("Skip video `%s` - no description", file.name)
            return []

        return VideoTextSplitter(
            url=lambda chapter: f"{sharepoint_url}/_layouts/15/embed.aspx?UniqueId={base_metadata.get('sourceId', '')}&nav=%7B%22playbackOptions%22%3A%7B%22startTimeInSeconds%22%3A{chapter.start_time if chapter else 0}%7D%7D&embed=%7B%22ust%22%3Atrue%2C%22hv%22%3A%22CopyEmbedCode%22%7D&referrer=StreamWebApp&referrerScenario=EmbedDialog.Create",
            description=video_description,
            base_metadata=base_metadata,
        ).split()

    async def __create_pdf_documents(self, file: File, base_metadata: dict):
        local_directory = os.environ.get("LOCAL_DIRECTORY") or "./files"

        file_name = file.name

        logger.info("Create documents for PDF file `%s`", file_name)

        local_path = f"{local_directory}/{file_name}"
        await self._data_source.download_file(file, local_path)

        try:
            chunks = await PdfSplitter(
                local_path,
                base_metadata,
                chunking_config=self.__collection_config.get("chunking"),
            ).split()
        except Exception as e:
            raise e
        finally:
            os.remove(local_path)

        chunks_total = len(chunks)
        logger.info("File `%s` splitted into %s chunks", file_name, chunks_total)

        return chunks
