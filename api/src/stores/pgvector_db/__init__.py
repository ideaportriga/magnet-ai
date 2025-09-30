"""PgVector database store implementation."""

from core.config.base import get_vector_database_settings, get_general_settings
from .client import PgVectorClient
from .store import PgVectorStore
from .utils import clean_connection_string_for_asyncpg

__all__ = ["PgVectorClient", "PgVectorStore"]

# Initialize pgvector store if configured
general_settings = get_general_settings()
db_settings = get_vector_database_settings()

db_type = db_settings.VECTOR_DB_TYPE

if db_type == "PGVECTOR":
    connection_string = db_settings.PGVECTOR_CONNECTION_STRING
    if not connection_string:
        # Build connection string from individual components
        host = db_settings.PGVECTOR_HOST
        port = db_settings.PGVECTOR_PORT
        database = db_settings.PGVECTOR_DATABASE
        user = db_settings.PGVECTOR_USER
        password = db_settings.PGVECTOR_PASSWORD
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        # Clean up SQLAlchemy-style URLs for asyncpg compatibility
        connection_string = clean_connection_string_for_asyncpg(connection_string)

    pool_size = db_settings.PGVECTOR_POOL_SIZE

    pgvector_client = PgVectorClient(
        connection_string=connection_string,
        pool_size=pool_size,
    )

    pgvector_store = PgVectorStore(client=pgvector_client)

    # Export initialized instances
    __all__.extend(["pgvector_client", "pgvector_store"])
