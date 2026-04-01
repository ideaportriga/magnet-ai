"""Database engine factory with dialect-specific configuration.

Replaces the monolithic if/elif chain in DatabaseSettings.get_engine() with a
strategy pattern, making it straightforward to add Oracle, MSSQL, or other
backends without touching existing code paths.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from core.config.base import DatabaseSettings

logger = logging.getLogger(__name__)
pool_logger = logging.getLogger("magnet.db.pool")


def _attach_pool_logging(engine: AsyncEngine) -> None:
    """Attach event listeners that log pool checkout/checkin events.

    Logs at DEBUG for normal operations and WARNING when overflow is detected.
    """
    from sqlalchemy.pool import QueuePool

    pool = engine.pool
    if not isinstance(pool, QueuePool):
        return

    @event.listens_for(pool, "checkout")
    def _on_checkout(
        dbapi_conn: Any, connection_record: Any, connection_proxy: Any
    ) -> None:
        overflow = pool.overflow()
        if overflow > 0:
            pool_logger.warning(
                "pool_checkout (overflow): checked_out=%d overflow=%d pool_size=%d",
                pool.checkedout(),
                overflow,
                pool.size(),
            )
        else:
            pool_logger.debug(
                "pool_checkout: checked_out=%d checked_in=%d",
                pool.checkedout(),
                pool.checkedin(),
            )

    @event.listens_for(pool, "checkin")
    def _on_checkin(dbapi_conn: Any, connection_record: Any) -> None:
        pool_logger.debug(
            "pool_checkin: checked_out=%d checked_in=%d",
            pool.checkedout(),
            pool.checkedin(),
        )


class AsyncEngineFactory(ABC):
    """Base class for dialect-specific engine factories."""

    @abstractmethod
    def create(self, url: str, settings: DatabaseSettings) -> AsyncEngine:
        """Create an AsyncEngine with dialect-appropriate options."""
        ...


class PostgresEngineFactory(AsyncEngineFactory):
    #: Session-level idle-in-transaction timeout (ms).  Kills connections that
    #: hold an open transaction without activity, preventing pool slot leaks.
    IDLE_IN_TRANSACTION_TIMEOUT_MS = 120_000  # 2 minutes

    def create(self, url: str, settings: DatabaseSettings) -> AsyncEngine:
        engine = create_async_engine(
            url=url,
            future=True,
            json_serializer=settings._json_serializer(),
            json_deserializer=settings._json_deserializer(),
            echo=settings.ECHO,
            echo_pool=settings.ECHO_POOL,
            max_overflow=settings.POOL_MAX_OVERFLOW,
            pool_size=settings.POOL_SIZE,
            pool_timeout=settings.POOL_TIMEOUT,
            pool_recycle=settings.POOL_RECYCLE,
            pool_pre_ping=settings.POOL_PRE_PING,
            pool_use_lifo=True,
            poolclass=NullPool if settings.POOL_DISABLED else None,
        )

        # Set session-level idle_in_transaction_session_timeout so PostgreSQL
        # auto-kills connections that forget to commit/rollback.
        timeout_ms = self.IDLE_IN_TRANSACTION_TIMEOUT_MS

        @event.listens_for(engine.sync_engine, "connect")
        def _set_idle_timeout(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET idle_in_transaction_session_timeout = '{timeout_ms}'")
            cursor.close()

        _attach_pool_logging(engine)
        return engine


class SQLiteEngineFactory(AsyncEngineFactory):
    def create(self, url: str, settings: DatabaseSettings) -> AsyncEngine:
        engine = create_async_engine(
            url=url,
            future=True,
            json_serializer=settings._json_serializer(),
            json_deserializer=settings._json_deserializer(),
            echo=settings.ECHO,
            echo_pool=settings.ECHO_POOL,
            pool_recycle=settings.POOL_RECYCLE,
            pool_pre_ping=settings.POOL_PRE_PING,
        )

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:
            dbapi_connection.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def _sqla_on_begin(dbapi_connection: Any) -> Any:
            dbapi_connection.exec_driver_sql("BEGIN")

        return engine


class OracleEngineFactory(AsyncEngineFactory):
    def create(self, url: str, settings: DatabaseSettings) -> AsyncEngine:
        return create_async_engine(
            url=url,
            future=True,
            json_serializer=settings._json_serializer(),
            json_deserializer=settings._json_deserializer(),
            echo=settings.ECHO,
            echo_pool=settings.ECHO_POOL,
            max_overflow=settings.POOL_MAX_OVERFLOW,
            pool_size=settings.POOL_SIZE,
            pool_timeout=settings.POOL_TIMEOUT,
            pool_recycle=settings.POOL_RECYCLE,
            pool_pre_ping=settings.POOL_PRE_PING,
            pool_use_lifo=True,
            poolclass=NullPool if settings.POOL_DISABLED else None,
        )


class MSSQLEngineFactory(AsyncEngineFactory):
    """MSSQL-specific factory.

    Uses aioodbc driver. Pool settings may need tuning vs PostgreSQL.
    """

    def create(self, url: str, settings: DatabaseSettings) -> AsyncEngine:
        return create_async_engine(
            url=url,
            future=True,
            json_serializer=settings._json_serializer(),
            json_deserializer=settings._json_deserializer(),
            echo=settings.ECHO,
            echo_pool=settings.ECHO_POOL,
            max_overflow=settings.POOL_MAX_OVERFLOW,
            pool_size=settings.POOL_SIZE,
            pool_timeout=settings.POOL_TIMEOUT,
            pool_recycle=settings.POOL_RECYCLE,
            pool_pre_ping=settings.POOL_PRE_PING,
            pool_use_lifo=True,
            poolclass=NullPool if settings.POOL_DISABLED else None,
        )


# Registry: URL prefix → factory instance
_FACTORIES: dict[str, AsyncEngineFactory] = {
    "postgresql": PostgresEngineFactory(),
    "sqlite": SQLiteEngineFactory(),
    "oracle": OracleEngineFactory(),
    "mssql": MSSQLEngineFactory(),
}


def get_engine_factory(url: str) -> AsyncEngineFactory:
    """Select the appropriate factory based on the database URL prefix."""
    for prefix, factory in _FACTORIES.items():
        if prefix in url:
            return factory
    # Fallback — use PostgreSQL-like config for unknown drivers
    logger.warning(
        "No specific engine factory for URL prefix, using PostgreSQL defaults"
    )
    return PostgresEngineFactory()
