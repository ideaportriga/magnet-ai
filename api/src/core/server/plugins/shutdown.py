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

        # Shutdown scheduler
        await self._shutdown_scheduler(app)

        # Drain in-flight knowledge-graph extraction tasks so they get a chance
        # to write a final "interrupted" status to the DB. Without this drain,
        # the previous 0.5s sleep killed running extractions with no log and
        # left their state stuck on "running" forever.
        await self._drain_extraction_tasks()

        # Close database connection pools
        await self._close_database_connections()

    @staticmethod
    async def _drain_extraction_tasks() -> None:
        """Wait up to DRAIN_TIMEOUT for active extraction tasks to finish."""
        DRAIN_TIMEOUT = 30.0

        try:
            from services.knowledge_graph.llm_entity_extraction import (
                _active_extraction_tasks,
            )
        except Exception:
            _active_extraction_tasks = {}
        try:
            from services.knowledge_graph.llm_metadata_extraction import (
                _active_metadata_tasks,
            )
        except Exception:
            _active_metadata_tasks = {}
        try:
            from services.knowledge_graph.sources.sync_services import (
                _active_sync_tasks,
            )
        except Exception:
            _active_sync_tasks = {}

        tasks = [
            *list(_active_extraction_tasks.values()),
            *list(_active_metadata_tasks.values()),
            *list(_active_sync_tasks.values()),
        ]
        # Filter out anything already done.
        tasks = [t for t in tasks if t is not None and not t.done()]

        if not tasks:
            logger.info("Shutdown: no in-flight extraction tasks to drain")
            return

        logger.info(
            "Shutdown: draining %d in-flight extraction task(s), up to %.0fs",
            len(tasks),
            DRAIN_TIMEOUT,
        )

        try:
            done, pending = await asyncio.wait(tasks, timeout=DRAIN_TIMEOUT)
        except Exception:
            logger.exception("Shutdown: error while awaiting extraction tasks")
            return

        logger.info(
            "Shutdown: %d extraction task(s) completed during drain, %d still pending",
            len(done),
            len(pending),
        )

        # Cancel anything still pending so the loop can shut down cleanly.
        # The wrappers handle CancelledError and write 'interrupted' status.
        for t in pending:
            t.cancel()
        if pending:
            try:
                await asyncio.wait(pending, timeout=5.0)
            except Exception:
                logger.exception(
                    "Shutdown: error while awaiting cancelled extraction tasks"
                )

    async def _shutdown_scheduler(self, app: Litestar) -> None:
        """Shutdown the scheduler."""
        scheduler = getattr(app.state, "scheduler", None)
        if scheduler is not None:
            try:
                logger.info("Shutting down scheduler...")
                # Try with wait parameter first, fallback to basic shutdown if not supported
                try:
                    scheduler.shutdown(wait=True)  # Wait for current jobs to complete
                except TypeError:
                    # Fallback for schedulers that don't support wait parameter
                    scheduler.shutdown()
                logger.info("Scheduler shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {e}")
        else:
            logger.info("No scheduler to shut down")

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
