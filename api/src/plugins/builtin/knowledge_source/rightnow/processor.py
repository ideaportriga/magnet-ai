"""RightNow Data Processor

This processor handles the transformation of RightNow knowledge base articles into document chunks.
"""

from data_sources.rightnow.source import RightNowDataSource
from data_sources.rightnow.types import Answer
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from models import DocumentData


class RightNowDataProcessor(DataProcessor):
    """Data processor for RightNow knowledge base"""

    __data_source: RightNowDataSource
    __records: list[Answer]

    def __init__(self, data_source: RightNowDataSource) -> None:
        self.__data_source = data_source

    @property
    def data_source(self) -> RightNowDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        self.__records = await self.__data_source.get_data()

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        return [
            SourceBasicMetadata(
                source_id=str(record.id),
                title=record.summary or "",
                modified_date=record.updated_time,
            )
            for record in self.__records
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        record = next(
            (record for record in self.__records if str(record.id) == id),
            None,
        )

        if not record:
            raise Exception(f"Record with id {id} not found")

        return [
            document
            for document in self.create_documents_from_plain_text(
                self.__process_record(record),
                self.__create_base_metadata(record),
            )
        ]

    def __create_base_metadata(self, record: Answer) -> dict:
        source = (
            f"{self.__data_source.instance_url}/app/answers/detail/a_id/{record.id}"
        )

        return {
            "sourceId": record.id,
            "name": record.summary,
            "source": source,
            "title": record.summary,
            "createdTime": record.created_time,
            "modifiedTime": record.updated_time,
        }

    def __process_record(self, record: Answer) -> str:
        result = f"Question: {self._html_to_text(record.question or '')}\n\nSolution: {self._html_to_text(record.solution or '')}"
        return result
