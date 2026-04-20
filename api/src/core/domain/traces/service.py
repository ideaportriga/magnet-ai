from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service
from advanced_alchemy.filters import FilterTypes
from sqlalchemy import func, or_
from sqlalchemy.orm import defer

from core.db.models.trace import Trace


class JsonbPathFilter:
    """Custom filter for JSONB path filtering that works with advanced-alchemy.

    Uses `jsonb_extract_path_text` rather than chained subscript (`col[a][b].astext`)
    because advanced_alchemy's JsonB wrapper loses its JSON type after the second
    subscript — the operand becomes a plain BinaryExpression and `.astext` raises
    AttributeError at query build time. The function form is PG-native, supports
    arbitrary nesting, and returns text directly for the `== value` comparison.
    """

    # Known nested paths that map to a logical filter key. Extend as needed.
    _NESTED_PATHS: dict[str, tuple[str, ...]] = {
        "system_name": ("params", "system_name"),
    }

    def __init__(self, json_field: str, json_path: str, values: list[str]):
        self.json_field = json_field
        self.json_path = json_path
        self.values = values

    def _path_parts(self) -> tuple[str, ...]:
        return self._NESTED_PATHS.get(self.json_path, (self.json_path,))

    def append_to_statement(self, statement, model_type: type[Trace]):
        """Append JSONB filter condition to the statement."""
        parts = self._path_parts()
        path_expr = func.jsonb_extract_path_text(Trace.extra_data, *parts)
        conditions = [path_expr == value for value in self.values]

        if len(conditions) == 1:
            return statement.where(conditions[0])
        return statement.where(or_(*conditions))


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
        load_options = [defer(Trace.spans)]

        # If no JSONB filters, use standard method
        if not jsonb_filters:
            results, total = await self.list_and_count(*filters, load=load_options)
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
        results, total = await self.list_and_count(*all_filters, load=load_options)

        return list(results), total
