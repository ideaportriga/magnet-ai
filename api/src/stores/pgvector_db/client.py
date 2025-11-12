"""PostgreSQL client with pgvector support."""

import asyncio
import json
import logging
from typing import Any

import asyncpg
from asyncpg import Connection, Pool
from pgvector.asyncpg import register_vector

from .utils import mask_password_in_connection_string

logger = logging.getLogger(__name__)


async def _setup_connection_types(connection: Connection) -> None:
    """Setup custom type decoders for the connection."""
    # Set up JSONB decoder to return dict instead of str
    await connection.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )

    # Also set up JSON decoder
    await connection.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    # Try to register pgvector codec, but don't fail if extension is missing yet
    try:
        await register_vector(connection)
    except Exception as e:  # asyncpg raises ValueError("unknown type: public.vector")
        msg = str(e).lower()
        if "unknown type" in msg and "vector" in msg:
            logger.warning(
                "pgvector extension not available yet; skipping type registration on this connection"
            )
        else:
            # Re-raise unexpected errors
            raise


class PgVectorClient:
    """Client for PostgreSQL with pgvector extension."""

    def __init__(self, connection_string: str, pool_size: int = 10):
        """Initialize the PostgreSQL client.

        Args:
            connection_string: PostgreSQL connection string
            pool_size: Maximum number of connections in the pool
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool: Pool | None = None
        self._initialization_started = False

    async def _ensure_pool_initialized(self) -> None:
        """Ensure the connection pool is initialized."""
        if self.pool is None and not self._initialization_started:
            await self.init_pool()

    async def init_pool(self) -> None:
        """Initialize the connection pool."""
        if self._initialization_started or self.pool is not None:
            return

        self._initialization_started = True
        logger.info("Initializing PostgreSQL connection pool")

        # Log connection string (without password for security)
        safe_connection_string = mask_password_in_connection_string(
            self.connection_string
        )
        logger.info(f"Using connection string: {safe_connection_string}")

        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=60,
                init=_setup_connection_types,  # Set up type decoders for each connection
            )
            logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL connection pool: %s", e)
            self._initialization_started = False
            raise

    async def close_pool(self) -> None:
        """Close the connection pool."""
        if self.pool:
            try:
                await asyncio.wait_for(self.pool.close(), timeout=5.0)
                self.pool = None
                logger.info("PostgreSQL connection pool closed")
            except asyncio.TimeoutError:
                logger.warning("Connection pool close timed out")
                self.pool = None
            except Exception as e:
                logger.error("Error closing connection pool: %s", e)
                self.pool = None

    async def get_connection(self) -> Connection:
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized")
        return await self.pool.acquire()

    async def release_connection(self, connection: Connection) -> None:
        """Release a connection back to the pool."""
        if self.pool:
            await self.pool.release(connection)

    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return the result."""
        await self._ensure_pool_initialized()
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized")
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetch(query, *args)
        except asyncio.CancelledError:
            logger.debug("Query execution was cancelled")
            raise
        except Exception as e:
            logger.error("Error executing query: %s", e)
            raise

    async def execute_command(self, command: str, *args) -> Any:
        """Execute a command (INSERT, UPDATE, DELETE) and return the result."""
        await self._ensure_pool_initialized()
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized")
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(command, *args)
        except asyncio.CancelledError:
            logger.debug("Command execution was cancelled")
            raise
        except Exception as e:
            logger.error("Error executing command: %s", e)
            raise

    async def fetchrow(self, query: str, *args) -> Any:
        """Fetch a single row."""
        await self._ensure_pool_initialized()
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized")
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchrow(query, *args)
        except asyncio.CancelledError:
            logger.debug("Fetchrow was cancelled")
            raise
        except Exception as e:
            logger.error("Error fetching row: %s", e)
            raise

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        await self._ensure_pool_initialized()
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized")
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchval(query, *args)
        except asyncio.CancelledError:
            logger.debug("Fetchval was cancelled")
            raise
        except Exception as e:
            logger.error("Error fetching value: %s", e)
            raise

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
            # After installing the extension, ensure the current pool connection(s)
            # have the vector codec registered
            try:
                if self.pool:
                    async with self.pool.acquire() as connection:
                        await register_vector(connection)
                        logger.info("pgvector type codec registered on pool connection")
            except Exception as e:
                logger.warning(
                    "Failed to register pgvector codec after installation: %s", e
                )
        else:
            logger.info("pgvector extension is already installed")
