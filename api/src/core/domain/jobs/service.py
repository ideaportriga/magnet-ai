from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service
from advanced_alchemy.filters import FilterTypes
from sqlalchemy import or_

from core.db.models.job import Job


class JsonbDefinitionFilter:
    """Cross-dialect JSONB filter for Job.definition field."""

    def __init__(self, json_key: str, values: list[str]):
        self.json_key = json_key
        self.values = values

    def append_to_statement(self, statement, model_type: type[Job]):
        conditions = []
        for value in self.values:
            if self.json_key == "run_configuration_type":
                expr = Job.definition["run_configuration"]["type"].astext == value
            else:
                expr = Job.definition[self.json_key].astext == value
            conditions.append(expr)

        if len(conditions) == 1:
            return statement.where(conditions[0])
        return statement.where(or_(*conditions))


class JobsService(service.SQLAlchemyAsyncRepositoryService[Job]):
    """Jobs service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Job]):
        """Jobs repository."""

        model_type = Job

    repository_type = Repo

    async def list_and_count_with_jsonb_filters(
        self,
        *filters: FilterTypes,
        jsonb_filters: dict[str, list[str]] | None = None,
    ) -> tuple[list[Job], int]:
        """Custom method to handle JSONB field filtering for the definition field."""
        if not jsonb_filters:
            results, total = await self.list_and_count(*filters)
            return list(results), total

        additional_filters = []
        for json_key, values in jsonb_filters.items():
            if values:
                additional_filters.append(JsonbDefinitionFilter(json_key, values))

        all_filters = list(filters) + additional_filters
        results, total = await self.list_and_count(*all_filters)
        return list(results), total
