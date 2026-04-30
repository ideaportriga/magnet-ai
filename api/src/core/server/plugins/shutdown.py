"""Shutdown plugin for handling application cleanup."""

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

        # Cancel background monitors started in startup plugin
        await self._cancel_event_loop_monitor(app)

        # Shutdown the TaskIQ broker on the API process. Worker/scheduler
        # processes handle their own broker lifecycle via the CLI.
        await self._shutdown_taskiq_broker(app)

        # Flush OTEL traces so spans reach the collector before the engine
        # (and the shared sync span-exporter engine) is torn down. §C.7.
        await self._flush_otel_traces()

        # Close shared HTTP client
        await self._close_http_client()

        # Close vector DB connection pools
        await self._close_vector_db_connections()

        # Dispose the main ORM engine (returns all connections to the OS)
        await self._close_main_engine()

    @staticmethod
    async def _cancel_event_loop_monitor(app: Litestar) -> None:
        import asyncio

        task = getattr(app.state, "event_loop_monitor_task", None)
        if task is None:
            return
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    @staticmethod
    async def _flush_otel_traces() -> None:
        """Force-flush OpenTelemetry tracer provider so pending spans are exported
        before we dispose the shared sync engine that some exporters write through.
        See BACKEND_FIXES_ROADMAP.md §C.7.
        """
        try:
            from opentelemetry import trace

            provider = trace.get_tracer_provider()
            flush = getattr(provider, "force_flush", None)
            if callable(flush):
                flush(timeout_millis=5000)
                logger.info("OTEL tracer provider flushed")
        except Exception as e:
            logger.warning("OTEL flush failed: %s", e)

    @staticmethod
    async def _shutdown_taskiq_broker(app: Litestar) -> None:
        try:
            broker = getattr(app.state, "taskiq_broker", None)
            if broker is None:
                return
            # `TaskiqRuntimePlugin` flips `is_worker_process=True` during
            # in-process startup; we still own the broker lifecycle and
            # must close the asyncpg pools here. The previous
            # `if is_worker_process: return` guard belonged to the
            # multi-container era and is wrong for in-process.
            await broker.shutdown()
            logger.info("TaskIQ broker shut down")
        except Exception as exc:  # noqa: BLE001
            logger.error("Error shutting down TaskIQ broker: %s", exc)

    async def _close_http_client(self) -> None:
        """Close the shared httpx.AsyncClient."""
        try:
            from utils.http_client import close_http_client

            await close_http_client()
            logger.info("Shared HTTP client closed")
        except Exception as e:
            logger.error("Error closing shared HTTP client: %s", e)

    async def _close_main_engine(self) -> None:
        """Dispose the main async engine and all managed engines."""
        try:
            from core.db.connection_manager import get_connection_manager

            await get_connection_manager().close_all()
            logger.info("Main database engines disposed successfully")
        except Exception as e:
            logger.error("Error disposing main database engines: %s", e)

    async def _close_vector_db_connections(self) -> None:
        """Close vector DB connection pools based on VECTOR_DB_TYPE."""
        if self.db_type == "ORACLE":
            await self._close_oracle_connections()
        elif self.db_type == "PGVECTOR":
            await self._close_pgvector_connections()

    async def _close_oracle_connections(self) -> None:
        """Close Oracle connection pool."""
        logger.info("Closing Oracle connection pool...")
        try:
            from stores import get_db_client

            client = get_db_client()
            await client.close_pool()
            logger.info("Oracle connection pool closed successfully")
        except Exception as e:
            logger.error("Error closing Oracle connection pool: %s", e)

    async def _close_pgvector_connections(self) -> None:
        """Close PgVector connection pool."""
        logger.info("Closing PgVector connection pool...")
        try:
            from stores.pgvector_db import pgvector_client

            await pgvector_client.close_pool()
            logger.info("PgVector connection pool closed successfully")
        except Exception as e:
            logger.error("Error closing PgVector connection pool: %s", e)
