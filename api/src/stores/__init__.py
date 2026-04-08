# Async compatibility check: True

from core.config.base import get_vector_database_settings
from stores.document_store import DocumentStore


from core.exceptions import NotFoundError


class RecordNotFoundError(NotFoundError):
    """Record not found in a document / vector store."""


def get_db_client():
    """Return the low-level vector DB client for the default store.

    Prefer ``get_db_store()`` or ``get_vector_store_registry().get(name)``
    for new code.
    """
    db_settings = get_vector_database_settings()
    db_type = db_settings.VECTOR_DB_TYPE

    if db_type == "ORACLE":
        from stores.oracle import oracle_db_client

        return oracle_db_client
    if db_type == "COSMOS":
        from stores.cosmos_db import cosmos_db_client

        return cosmos_db_client
    if db_type == "PGVECTOR":
        from stores.pgvector_db import pgvector_client

        return pgvector_client
    raise ValueError(f"Unsupported VECTOR_DB_TYPE: {db_type}")


def get_db_store() -> DocumentStore:
    """Return the default vector document store.

    This delegates to ``VectorStoreRegistry`` if a default store has been
    registered (happens during application startup).  Falls back to direct
    instantiation for backward compatibility during tests / CLI scripts.
    """
    from stores.registry import get_vector_store_registry

    registry = get_vector_store_registry()
    if registry.has("default"):
        return registry.default

    # Fallback: direct lookup (backward compat for tests / CLI)
    db_settings = get_vector_database_settings()
    db_type = db_settings.VECTOR_DB_TYPE

    if db_type == "ORACLE":
        from stores.oracle import oracle_db_store

        return oracle_db_store
    if db_type == "COSMOS":
        from stores.cosmos_db import cosmos_db_store

        return cosmos_db_store
    if db_type == "PGVECTOR":
        from stores.pgvector_db import pgvector_store

        return pgvector_store
    raise ValueError(f"Unsupported VECTOR_DB_TYPE: {db_type}")
