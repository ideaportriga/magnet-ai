from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service
from advanced_alchemy.filters import FilterTypes
from sqlalchemy import text

from core.db.models.trace import Trace


class JsonbPathFilter:
    """Custom filter for JSONB path filtering that works with advanced-alchemy."""

    def __init__(self, json_field: str, json_path: str, values: list[str]):
        self.json_field = json_field
        self.json_path = json_path
        self.values = values

    def append_to_statement(self, statement, model_type: type[Trace]):
        """Append JSONB filter condition to the statement."""
        # Create OR conditions for multiple values using parameterized queries
        condition_strings = []
        params = {}

        for i, value in enumerate(self.values):
            param_name = f"{self.json_path}_value_{i}"
            params[param_name] = value

            if self.json_path == "system_name":
                # For nested path: extra_data->'params'->>'system_name'
                condition_strings.append(
                    f"extra_data->'params'->>'system_name' = :{param_name}"
                )
            else:
                # For direct path: extra_data->>'key'
                condition_strings.append(
                    f"extra_data->>'{self.json_path}' = :{param_name}"
                )

        # Combine with OR if multiple values
        if len(condition_strings) == 1:
            filter_condition = text(condition_strings[0]).params(**params)
        else:
            combined_condition = " OR ".join(condition_strings)
            filter_condition = text(f"({combined_condition})").params(**params)

        return statement.where(filter_condition)


class TracesService(service.SQLAlchemyAsyncRepositoryService[Trace]):
    """Traces service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Trace]):
        """Traces repository."""

        model_type = Trace

    repository_type = Repo

    async def list_and_count_with_jsonb_filters(
        self,
        *filters: FilterTypes,
        jsonb_filters: dict[str, list[str]] | None = None,
    ) -> tuple[list[Trace], int]:
        """
        Enhanced method to handle JSONB field filtering while preserving all
        advanced-alchemy functionality including sorting, pagination, etc.

        Args:
            *filters: Standard advanced_alchemy filters
            jsonb_filters: Dictionary mapping JSON keys to values for filtering

        Returns:
            Tuple of (filtered traces list, total count)
        """
        # If no JSONB filters, use standard method
        if not jsonb_filters:
            results, total = await self.list_and_count(*filters)
            return list(results), total

        # Create JSONB filters using our custom filter class
        additional_filters = []

        for json_key, values in jsonb_filters.items():
            if values:  # Only add filter if values are provided
                jsonb_filter = JsonbPathFilter(
                    json_field="extra_data", json_path=json_key, values=values
                )
                additional_filters.append(jsonb_filter)

        # Combine all filters and use standard list_and_count method
        all_filters = list(filters) + additional_filters
        results, total = await self.list_and_count(*all_filters)

        return list(results), total
