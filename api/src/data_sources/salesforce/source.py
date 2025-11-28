import asyncio
import re

from simple_salesforce import Salesforce

from data_sources.data_source import DataSource


class SalesforceDataSource(DataSource[dict]):
    def __init__(
        self,
        salesforce: Salesforce,
        object_api_name: str,
        output_config: list[str],
    ) -> None:
        self.__salesforce = salesforce

        self.__validate_object_api_name(object_api_name)
        self.__object_api_name = object_api_name

        columns_to_select = self.__get_columns_to_select(output_config)
        self.__validate_columns_to_select(columns_to_select)
        self.__columns_to_select = columns_to_select

    @property
    def name(self) -> str:
        return "Salesforce"

    @property
    def salesforce_instance(self):
        return self.__salesforce.sf_instance

    @property
    def salesforce_object_api_name(self):
        return self.__object_api_name

    async def get_data(self) -> list[dict]:
        query = f"SELECT Id, CreatedDate, LastModifiedDate, Title, {', '.join(self.__columns_to_select)} \
                    FROM {self.__object_api_name} WHERE PublishStatus = 'Online'"

        # Wrap the synchronous call in asyncio.to_thread to avoid blocking
        try:
            result = await asyncio.to_thread(self.__salesforce.query_all, query)
        except Exception:
            # Handle exceptions as needed, e.g., log or re-raise
            raise

        return result.get("records", [])

    def __validate_object_api_name(self, object_api_name: str):
        pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*__kav$")

        if not pattern.match(object_api_name):
            raise ValueError(f"Invalid object API name: {object_api_name}")

    def __get_columns_to_select(self, output_config: list[str]) -> set[str]:
        result: list[str] = []

        for config in output_config:
            columns = re.findall(r"\{([^}]+)\}", config)

            result.extend(columns)

        return set(result)

    def __validate_columns_to_select(self, columns_to_select: set):
        pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*(?:__c)?$")

        for name in columns_to_select:
            if not pattern.match(name):
                raise ValueError(f"Invalid column name: {name}")
