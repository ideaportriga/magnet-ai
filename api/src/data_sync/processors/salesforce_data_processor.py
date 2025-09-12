import re

from data_sources.salesforce.source import SalesforceDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from data_sync.processors.types.salesforce_output_config import SalesforceOutputConfig
from models import DocumentData


class SalesforceDataProcessor(DataProcessor):
    __data_source: SalesforceDataSource
    __records: list[dict]

    def __init__(
        self,
        data_source: SalesforceDataSource,
        output_config: list[str],
    ) -> None:
        self.__data_source = data_source
        self.__config = [
            SalesforceOutputConfig(re.findall(r"\{([^}]+)\}", config), config)
            for config in output_config
        ]

    @property
    def data_source(self) -> SalesforceDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        self.__records = await self.__data_source.get_data()

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        return [
            SourceBasicMetadata(
                source_id=record_dict.get("Id", ""),
                title=record_dict.get("Title", ""),
                modified_date=record_dict.get("LastModifiedDate", ""),
            )
            for record_dict in self.__records
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        record = next(
            (record for record in self.__records if record.get("Id") == id),
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

    def __create_base_metadata(self, record: dict) -> dict:
        sourceId = record.get("Id")
        salesforce_instance = self.__data_source.salesforce_instance
        salesforce_object_api_name = self.__data_source.salesforce_object_api_name
        source = f"https://{salesforce_instance}/lightning/r/{salesforce_object_api_name}/{sourceId}/view"

        return {
            "sourceId": sourceId,
            "name": record.get("Title"),
            "source": source,
            "title": record.get("Title"),
            "createdTime": record.get("CreatedDate"),
            "modifiedTime": record.get("LastModifiedDate"),
        }

    def __process_record(self, record: dict) -> str:
        output_template = self.__get_output_template(record)

        if output_template is None:
            raise ValueError("Couldn't determine output template")

        result = output_template.format(**record)

        return result

    def __get_output_template(self, record: dict) -> str | None:
        for item in self.__config:
            all_columns_present_and_not_none = True

            for column in item.columns:
                if column not in record or record[column] is None:
                    all_columns_present_and_not_none = False
                    break

            if all_columns_present_and_not_none:
                return item.output_template

        return None
