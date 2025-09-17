from logging import getLogger

from langchain.schema import Document
from office365.sharepoint.files.file import File

from data_sources.sharepoint.source_pages import SharePointPagesDataSource
from data_sync.processors.sharepoint.sharepoint_abstract_data_processor import (
    SharepointAbstractDataProcessor,
)
from data_sync.splitters.html_splitter import HtmlSplitter
from data_sync.utils import clean_text, parse_page
from models import DocumentData

logger = getLogger(__name__)


class SharepointPagesDataProcessor(SharepointAbstractDataProcessor):
    def __init__(
        self,
        data_source: SharePointPagesDataSource,
        collection_config: dict,
        embed_title: bool = False,
    ) -> None:
        super().__init__(data_source)
        self.__collection_config = collection_config
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

            documents = await self._create_site_page_documents(
                base_metadata=base_metadata,
                file=file,
                base_url=base_url,
                embed_title=embed_title,
            )

            document_data_to_add.extend(
                [
                    DocumentData(content=doc.page_content, metadata=doc.metadata)
                    for doc in documents
                ]
            )

        return document_data_to_add

    async def _create_site_page_documents(
        self, file: File, base_metadata: dict, base_url: str, embed_title: bool
    ) -> list[Document]:
        file_name = file.name
        title = base_metadata.get("title", "")

        logger.info("Create documents for site page `%s`", file_name)

        # TODO - do we need also "LayoutWebpartsContent" prop for other page types?
        list_item = (
            file.listItemAllFields.select(["CanvasContent1"]).get().execute_query()
        )

        page_content = list_item.properties.get("CanvasContent1")

        chunks = []
        if page_content:
            if embed_title:
                cleaned_content = clean_text(
                    parse_page(page_content=page_content, base_url=base_url)
                )
                chunks = [
                    Document(
                        title,
                        metadata={
                            **base_metadata,
                            "content": {
                                "unmodified": cleaned_content,
                                "retrieval": cleaned_content,
                            },
                        },
                    )
                ]
            else:
                chunks = await HtmlSplitter(
                    page_content,
                    base_url=base_url,
                    base_metadata=base_metadata,
                    chunking_config=self.__collection_config.get("chunking"),
                ).split()

        logger.info(
            "Sharepoint site page `%s` splitted into %s chunks", file_name, len(chunks)
        )
        return chunks
