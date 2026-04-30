"""Database engine factory with dialect-specific configuration.

Replaces the monolithic if/elif chain in DatabaseSettings.get_engine() with a
strategy pattern, making it straightforward to add Oracle, MSSQL, or other
backends without touching existing code paths.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from asyncpg import Connection as AsyncpgConnection
    from core.config.base import DatabaseSettings

logger = logging.getLogger(__name__)
pool_logger = logging.getLogger("magnet.db.pool")


def _jsonb_encoder(value: Any) -> str:
    """Idempotent JSONB encoder.

    SQLAlchemy's engine-level ``json_serializer`` already converts dict/list
    to a JSON string before the value reaches asyncpg. If we then re-encode
    it via ``json.dumps``, the column ends up holding a JSON-stringified-JSON
    (e.g. ``'"[{...}]"'`` instead of the array), which Pydantic later rejects
    as ``input_value='[...]', input_type=str`` for ``list[...]`` fields.

    Direct asyncpg paths (e.g. ``PgVectorClient``) still pass raw dict/list,
    so we keep ``json.dumps`` for non-string values.
    """
    if isinstance(value, str):
        return value
    return json.dumps(value)


async def _register_jsonb_codecs(conn: "AsyncpgConnection") -> None:
    """Register asyncpg type codecs for JSONB/JSON.

    Without this, JSONB columns sometimes round-trip as raw JSON strings
    instead of `dict` (depending on which code path first touched the
    connection). `PgVectorClient` registers the same codecs via its own
    per-connection cache, but that cache is keyed by `id(conn)` which
    Python can reuse after GC, so it cannot guarantee coverage.
    """
    await conn.set_type_codec(
        "jsonb",
        encoder=_jsonb_encoder,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=_jsonb_encoder,
        decoder=json.loads,
        schema="pg_catalog",
    )


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
        timeout_ms = self.IDLE_IN_TRANSACTION_TIMEOUT_MS
        # asyncpg's server_settings are applied at connect time via the
        # PostgreSQL startup packet — they reliably enforce session-level
        # idle_in_transaction_session_timeout. The previous `@listens_for`
        # approach didn't fire for SQLAlchemy's async-wrapped asyncpg
        # connections, so leaked transactions accumulated across TaskIQ
        # worker task runs until the pool stalled.
        connect_args = {
            "server_settings": {
                "idle_in_transaction_session_timeout": str(timeout_ms),
                "application_name": "magnet-ai",
            },
        }
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
            connect_args=connect_args,
        )

        # Register JSONB/JSON codecs once per real asyncpg connection, before
        # any pool checkout runs query code. Done via SQLAlchemy's connect
        # event + AdaptedConnection.run_async because asyncpg.connect() (which
        # SQLAlchemy calls under the hood) does NOT accept asyncpg's pool-level
        # `init=` kwarg — passing it raises TypeError on every checkout.
        @event.listens_for(engine.sync_engine, "connect")
        def _on_connect(dbapi_connection: Any, _: Any) -> None:
            dbapi_connection.run_async(_register_jsonb_codecs)

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
