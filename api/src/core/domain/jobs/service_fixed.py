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

        # Create raw SQL WHERE conditions for JSONB fields
        jsonb_where_clauses = []

        for json_key, values in jsonb_filters.items():
            if values:
                # Create OR conditions for multiple values of the same key
                value_conditions = []
                for value in values:
                    # Use JSONB ->> operator for text comparison
                    value_conditions.append(f"definition->'{json_key}' = '{value}'")

                if value_conditions:
                    # Join with OR for multiple values
                    jsonb_where_clauses.append(f"({' OR '.join(value_conditions)})")

        # Combine all JSONB conditions with AND
        jsonb_where = " AND ".join(jsonb_where_clauses) if jsonb_where_clauses else ""

        # Use repository's session to execute raw queries
        async with self.repository.session as session:
            # Build queries
            select_clause = "SELECT * FROM jobs"
            count_clause = "SELECT COUNT(*) FROM jobs"

            if jsonb_where:
                where_clause = f" WHERE {jsonb_where}"
            else:
                where_clause = ""

            # Execute the main query
            result = await session.execute(text(select_clause + where_clause))
            items = [Job(**dict(row._mapping)) for row in result.fetchall()]

            # Execute count query
            count_result = await session.execute(text(count_clause + where_clause))
            total = count_result.scalar()

            return items, total or 0
