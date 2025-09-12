"""PgVector database store implementation."""

import os

from .client import PgVectorClient
from .store import PgVectorStore
from .utils import clean_connection_string_for_asyncpg

__all__ = ["PgVectorClient", "PgVectorStore"]

# Initialize pgvector store if configured
db_type = os.environ.get("DB_TYPE", "COSMOS")

if db_type == "PGVECTOR":
    connection_string = os.environ.get("PGVECTOR_CONNECTION_STRING", "")
    if not connection_string:
        # Build connection string from individual components
        host = os.environ.get("PGVECTOR_HOST", "localhost")
        port = os.environ.get("PGVECTOR_PORT", "5432")
        database = os.environ.get("PGVECTOR_DATABASE", "magnet_dev")
        user = os.environ.get("PGVECTOR_USER", "postgres")
        password = os.environ.get("PGVECTOR_PASSWORD", "password")
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        # Clean up SQLAlchemy-style URLs for asyncpg compatibility
        connection_string = clean_connection_string_for_asyncpg(connection_string)

    pool_size = int(os.environ.get("PGVECTOR_POOL_SIZE", "10"))

    pgvector_client = PgVectorClient(
        connection_string=connection_string,
        pool_size=pool_size,
    )

    pgvector_store = PgVectorStore(client=pgvector_client)

    # Export initialized instances
    __all__.extend(["pgvector_client", "pgvector_store"])
