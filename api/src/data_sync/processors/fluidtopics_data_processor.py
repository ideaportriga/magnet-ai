import os
from logging import getLogger

from data_sources.fluid_topics.source import FluidTopicsDataSource
from data_sources.fluid_topics.types import FluidTopicsDocument
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.splitters.pdf_splitter import PdfSplitter
from models import DocumentData

logger = getLogger(__name__)


class FluidTopicsDataProcessor(DataProcessor):
    """Class for processing data from Fluid Topics API."""

    __data_source: FluidTopicsDataSource
    __collection_config: dict
    __documents: list[FluidTopicsDocument]

    def __init__(
        self,
        data_source: FluidTopicsDataSource,
        collection_config: dict,
    ) -> None:
        """Initializes FluidTopicsDataProcessor with a FluidTopicsDataSource data source.

        Args:
            data_source (FluidTopicsDataSource): Data source with Fluid Topics search results.
            collection_config (dict): Collection configuration.

        """
        logger.info("Initializing FluidTopicsDataProcessor with provided data source.")
        self.__data_source = data_source
        self.__collection_config = collection_config

    @property
    def data_source(self) -> FluidTopicsDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        """Loads data from the data source and stores it in self.__urls."""
        logger.info("Loading data from the data source.")
        self.__documents = await self.__data_source.get_data()
        logger.info(f"Loaded {len(self.__documents)} files from the data source.")

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        return [
            SourceBasicMetadata(
                document.title or "",
                document.modified_date or "",
                document.id or "",
            )
            for document in self.__documents
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        """Creates documents for the given identifiers.

        Args:
            id (str): Unique identifier.

        Returns:
            List[DocumentData]: List of documents with metadata.

        """
        logger.info(f"Creating documents for {id}.")

        document = next(
            (document for document in self.__documents if document.id == id),
            None,
        )

        if not document:
            raise Exception(f"Document with id {id} not found")

        return await self.__process_file(document)

    async def __process_file(self, document: FluidTopicsDocument) -> list[DocumentData]:
        mime_type = document.mime_type
        if not mime_type:
            logger.warning("Cannot define file type as mime type is empty")
            return []

        document_data_to_add: list[DocumentData] = []

        base_metadata = self.__create_base_metadata(document)

        if mime_type == "application/pdf":
            local_directory = os.environ.get("LOCAL_DIRECTORY") or "./files"
            documents = await self.__create_pdf_documents(
                base_metadata=base_metadata,
                document=document,
                local_directory=local_directory,
            )
            document_data_to_add.extend(
                [
                    DocumentData(content=doc.page_content, metadata=doc.metadata)
                    for doc in documents
                ],
            )

        return document_data_to_add

    def __create_base_metadata(self, document: FluidTopicsDocument) -> dict:
        """Creates base metadata for a Fluid Topics document.

        Args:
            document (FluidTopicsDocument): Fluid Topics document.

        Returns:
            dict: Base metadata.

        """
        return {
            "sourceId": document.id,
            "name": document.title,
            "source": document.viewer_url,
            "title": document.title,
            "createdTime": document.created_date,
            "modifiedTime": document.modified_date,
        }

    # region PDF processing
    async def __create_pdf_documents(
        self,
        base_metadata: dict,
        document: FluidTopicsDocument,
        local_directory: str,
    ):
        file_name = document.file_name

        logger.info("Create documents for PDF file `%s`", file_name)

        local_path = f"{local_directory}/{file_name}"

        if not document.file_name:
            raise ValueError("File name is not set for document")

        url = await self.data_source.get_url(document.file_name)
        if not url:
            raise ValueError("Cannot get URL for the file")

        await self.data_source.download_file(url, local_path)

        try:
            chunks = await PdfSplitter(
                local_path,
                base_metadata,
                chunking_config=self.__collection_config.get("chunking"),
            ).split()
        except Exception:
            raise
        finally:
            os.remove(local_path)

        logger.info("File `%s` splitted into %s chunks", file_name, len(chunks))

        return chunks


# endregion
