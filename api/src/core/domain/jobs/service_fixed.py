from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service
from advanced_alchemy.filters import FilterTypes
from sqlalchemy import text

from core.db.models.job import Job


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
        """
        Custom method to handle JSONB field filtering for the definition field.

        Args:
            *filters: Standard advanced_alchemy filters
            jsonb_filters: Dictionary mapping JSON keys to values for filtering

        Returns:
            Tuple of (filtered jobs list, total count)
        """
        if not jsonb_filters:
            results, total = await self.list_and_count(*filters)
            return list(results), total

        # Build parameterized WHERE conditions for JSONB fields
        jsonb_where_clauses = []
        params: dict[str, str] = {}
        param_idx = 0

        for json_key, values in jsonb_filters.items():
            if not values:
                continue
            value_conditions = []
            for value in values:
                key_param = f"jk_{param_idx}"
                val_param = f"jv_{param_idx}"
                value_conditions.append(f"definition->>:{key_param} = :{val_param}")
                params[key_param] = json_key
                params[val_param] = value
                param_idx += 1

            if value_conditions:
                jsonb_where_clauses.append(f"({' OR '.join(value_conditions)})")

        jsonb_where = " AND ".join(jsonb_where_clauses) if jsonb_where_clauses else ""

        async with self.repository.session as session:
            select_clause = "SELECT * FROM jobs"
            count_clause = "SELECT COUNT(*) FROM jobs"
            where_clause = f" WHERE {jsonb_where}" if jsonb_where else ""

            result = await session.execute(text(select_clause + where_clause), params)
            items = [Job(**dict(row._mapping)) for row in result.fetchall()]

            count_result = await session.execute(
                text(count_clause + where_clause), params
            )
            total = count_result.scalar()

            return items, total or 0
