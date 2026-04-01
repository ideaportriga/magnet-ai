"""Database connection pool monitoring utilities."""

from __future__ import annotations

from typing import Any

from core.db.connection_manager import get_connection_manager


async def get_db_pool_status() -> dict[str, Any]:
    """Return pool metrics for all database engines.

    Can be exposed via an admin health-check endpoint, e.g.:

        @get("/admin/health/db")
        async def db_health() -> dict:
            return await get_db_pool_status()
    """
    return get_connection_manager().get_pool_status()
