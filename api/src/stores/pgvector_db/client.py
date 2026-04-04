"""PostgreSQL client with pgvector support.

Uses the main SQLAlchemy AsyncEngine connection pool instead of a separate asyncpg
pool. This eliminates ~10 extra connections and the race condition in pool init.
Raw asyncpg connections are obtained via engine.raw_connection() so existing $1/$2
parameter style SQL continues to work unchanged.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from asyncpg import Connection
from pgvector.asyncpg import register_vector
from sqlalchemy.ext.asyncio import AsyncEngine

from core.exceptions import VectorDBError

logger = logging.getLogger(__name__)


async def _setup_connection_types(connection: Connection) -> None:
    """Setup custom type decoders for the connection."""
    await connection.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    await connection.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    try:
        await register_vector(connection)
    except Exception as e:
        msg = str(e).lower()
        if "unknown type" in msg and "vector" in msg:
            logger.warning(
                "pgvector extension not available yet; skipping type registration on this connection"
            )
        else:
            raise


class PgVectorClient:
    """Client for PostgreSQL with pgvector extension.

    Delegates connection management to a SQLAlchemy AsyncEngine so that vector
    operations share the same connection pool as ORM operations.
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 10,
        engine: AsyncEngine | None = None,
    ):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self._engine = engine
        self._codecs_registered: set[int] = set()
        self._codec_lock = asyncio.Lock()
        # Legacy attribute — some callers check `client.pool`.
        # After migration it's always None; use _engine instead.
        self.pool = None

    def _get_engine(self) -> AsyncEngine:
        if self._engine is not None:
            return self._engine
        # Lazy import to avoid circular deps at module level
        from core.config.app import settings

        self._engine = settings.db.get_engine()
        return self._engine

    @asynccontextmanager
    async def _acquire(self):
        """Acquire a raw asyncpg connection from the SQLAlchemy engine pool."""
        engine = self._get_engine()
        async with engine.connect() as sa_conn:
            raw = await sa_conn.get_raw_connection()
            asyncpg_conn: Connection = raw.driver_connection
            # Register pgvector codecs once per underlying connection
            conn_id = id(asyncpg_conn)
            if conn_id not in self._codecs_registered:
                async with self._codec_lock:
                    if conn_id not in self._codecs_registered:
                        await _setup_connection_types(asyncpg_conn)
                        self._codecs_registered.add(conn_id)
            yield asyncpg_conn

    # -- Public API (same interface as before) ----------------------------------

    async def init_pool(self) -> None:
        """No-op. Pool is managed by the SQLAlchemy engine."""
        logger.info(
            "PgVectorClient: using SQLAlchemy engine pool (no separate pool to init)"
        )

    async def close_pool(self) -> None:
        """No-op. Pool lifecycle is managed by the SQLAlchemy engine."""

    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return the result."""
        try:
            async with self._acquire() as connection:
                return await connection.fetch(query, *args)
        except asyncio.CancelledError:
            raise
        except VectorDBError:
            raise
        except Exception as e:
            raise VectorDBError(f"PGVector query failed: {e}") from e

    async def execute_command(self, command: str, *args) -> Any:
        """Execute a command (INSERT, UPDATE, DELETE) and return the result."""
        try:
            async with self._acquire() as connection:
                return await connection.execute(command, *args)
        except asyncio.CancelledError:
            raise
        except VectorDBError:
            raise
        except Exception as e:
            raise VectorDBError(f"PGVector command failed: {e}") from e

    async def fetchrow(self, query: str, *args) -> Any:
        """Fetch a single row."""
        try:
            async with self._acquire() as connection:
                return await connection.fetchrow(query, *args)
        except asyncio.CancelledError:
            raise
        except VectorDBError:
            raise
        except Exception as e:
            raise VectorDBError(f"PGVector fetchrow failed: {e}") from e

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        try:
            async with self._acquire() as connection:
                return await connection.fetchval(query, *args)
        except asyncio.CancelledError:
            raise
        except VectorDBError:
            raise
        except Exception as e:
            raise VectorDBError(f"PGVector fetchval failed: {e}") from e

    async def check_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed."""
        try:
            result = await self.fetchrow(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            return result is not None
        except Exception as e:
            logger.error("Error checking pgvector extension: %s", e)
            return False

    async def ensure_pgvector_extension(self) -> None:
        """Ensure pgvector extension is installed."""
        if not await self.check_pgvector_extension():
            logger.info("Installing pgvector extension")
            await self.execute_command("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("pgvector extension installed")
        else:
            logger.info("pgvector extension is already installed")
