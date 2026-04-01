"""Centralized connection management for all database engines.

Principles:
- One main DB = one async engine (ORM + vector search when same DB)
- One shared sync engine for all sync-only components
- Extra engines only for genuinely separate DB instances (e.g. external vector DB)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, QueuePool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from core.config.base import (
    DatabaseSettings,
    get_settings,
)

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Single point of control for every SQLAlchemy engine in the application."""

    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings
        self._async_engine: AsyncEngine = settings.get_engine()
        self._sync_engine: Engine | None = None
        self._extra_engines: dict[str, AsyncEngine] = {}

    @property
    def async_engine(self) -> AsyncEngine:
        """Main async engine — ORM, KG services, PGVector (when same DB)."""
        return self._async_engine

    @property
    def sync_engine(self) -> Engine:
        """Shared sync engine — APScheduler, OTel exporter, Slack OAuth."""
        if self._sync_engine is None:
            from core.db.sync_engine import get_shared_sync_engine

            self._sync_engine = get_shared_sync_engine()
        return self._sync_engine

    def get_or_create_engine(self, name: str, url: str, **kwargs: Any) -> AsyncEngine:
        """Get or create a named async engine for a separate DB instance.

        If ``url`` matches the main engine URL the main engine is returned
        (no duplicate pool created).
        """
        if url == str(self._async_engine.url):
            return self._async_engine
        if name not in self._extra_engines:
            logger.info("Creating extra async engine %r", name)
            self._extra_engines[name] = create_async_engine(url, **kwargs)
        return self._extra_engines[name]

    # -- Monitoring -------------------------------------------------------------

    def get_pool_status(self) -> dict[str, Any]:
        """Return connection pool metrics for all managed engines."""
        result: dict[str, Any] = {
            "main_async": self._pool_info(self._async_engine),
        }
        if self._sync_engine is not None:
            result["shared_sync"] = self._pool_info(self._sync_engine)
        for name, engine in self._extra_engines.items():
            result[f"extra_{name}"] = self._pool_info(engine)
        return result

    @staticmethod
    def _pool_info(engine: AsyncEngine | Engine) -> dict[str, Any]:
        pool = engine.pool if isinstance(engine, Engine) else engine.pool
        if isinstance(pool, QueuePool):
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.checkedout() + pool.checkedin(),
            }
        return {"type": type(pool).__name__}

    # -- Lifecycle --------------------------------------------------------------

    async def close_all(self) -> None:
        """Graceful shutdown — dispose every engine."""
        logger.info("Disposing all database engines")
        await self._async_engine.dispose()
        if self._sync_engine is not None:
            self._sync_engine.dispose()
        for name, engine in self._extra_engines.items():
            logger.info("Disposing extra engine %r", name)
            await engine.dispose()
        self._extra_engines.clear()


@lru_cache(maxsize=1)
def get_connection_manager() -> DatabaseConnectionManager:
    """Return the global DatabaseConnectionManager singleton."""
    return DatabaseConnectionManager(get_settings().db)
