"""Shutdown plugin for handling application cleanup."""

import asyncio
import atexit
import os
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Litestar
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


class ShutdownPlugin(InitPluginProtocol):
    """Plugin to handle application shutdown logic."""

    def __init__(self) -> None:
        self.env = os.environ
        self.db_type = self.env.get("VECTOR_DB_TYPE")

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure app shutdown handlers."""
        shutdown_handlers = list(app_config.on_shutdown or [])
        shutdown_handlers.append(self._on_shutdown)
        app_config.on_shutdown = shutdown_handlers
        return app_config

    async def _on_shutdown(self, app: Litestar) -> None:
        """Application shutdown handler."""
        logger.info("Shutting down application...")

        # SAQ scheduler shutdown is managed by SAQPlugin (litestar-saq)

        # Give a brief moment for any ongoing operations to complete
        await asyncio.sleep(0.5)

        # Close database connection pools
        await self._close_database_connections()

    async def _close_database_connections(self) -> None:
        """Close database connection pools based on VECTOR_DB_TYPE."""
        if self.db_type == "ORACLE":
            await self._close_oracle_connections()
        elif self.db_type == "PGVECTOR":
            await self._close_pgvector_connections()

    async def _close_oracle_connections(self) -> None:
        """Close Oracle connection pool."""
        logger.info("Closing Oracle connection pool...")

        async def close_connection_pool():
            from stores import get_db_client

            client = get_db_client()
            await client.close_pool()

        atexit.register(close_connection_pool)

    async def _close_pgvector_connections(self) -> None:
        """Close PgVector connection pool."""
        logger.info("Closing PgVector connection pool...")
        try:
            from stores.pgvector_db import pgvector_client

            await pgvector_client.close_pool()
            logger.info("PgVector connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing PgVector connection pool: {e}")
