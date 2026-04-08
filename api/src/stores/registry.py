"""Registry of named vector store instances.

Allows the application to work with multiple vector databases simultaneously.
The "default" store uses the main DB engine when pgvector is available on the
same PostgreSQL instance.  Additional stores (Qdrant, separate PG, etc.) can
be registered at startup or dynamically via admin API.

Usage:

    registry = get_vector_store_registry()
    store = registry.get("default")           # main PGVector
    store = registry.get("qdrant-prod")       # external Qdrant cluster
    store = registry.default                  # shortcut for "default"
"""

from __future__ import annotations

import logging
from functools import lru_cache

from stores.document_store import DocumentStore

logger = logging.getLogger(__name__)


class VectorStoreRegistry:
    """Named registry of DocumentStore / VectorStore instances."""

    def __init__(self) -> None:
        self._stores: dict[str, DocumentStore] = {}

    def register(self, name: str, store: DocumentStore) -> None:
        """Register a named vector store (overwrites if name already exists)."""
        logger.info("Registered vector store %r (%s)", name, type(store).__name__)
        self._stores[name] = store

    def unregister(self, name: str) -> None:
        """Remove a store from the registry."""
        self._stores.pop(name, None)

    def get(self, name: str = "default") -> DocumentStore:
        """Get a vector store by name."""
        if name not in self._stores:
            available = list(self._stores.keys())
            raise KeyError(
                f"Vector store {name!r} not registered. Available: {available}"
            )
        return self._stores[name]

    @property
    def default(self) -> DocumentStore:
        """Shortcut for ``get("default")``."""
        return self.get("default")

    def has(self, name: str) -> bool:
        return name in self._stores

    def list_stores(self) -> dict[str, str]:
        """Return ``{name: class_name}`` for all registered stores."""
        return {name: type(store).__name__ for name, store in self._stores.items()}

    async def close_all(self) -> None:
        """Close all stores that have a ``close`` coroutine."""
        for name, store in self._stores.items():
            close = getattr(store, "close", None) or getattr(store, "close_pool", None)
            if close is not None and callable(close):
                try:
                    result = close()
                    # Handle both sync and async close
                    if hasattr(result, "__await__"):
                        await result
                except Exception:
                    logger.warning("Error closing vector store %r", name, exc_info=True)


@lru_cache(maxsize=1)
def get_vector_store_registry() -> VectorStoreRegistry:
    """Return the singleton VectorStoreRegistry.

    The registry is empty until stores are registered during application startup.
    """
    return VectorStoreRegistry()


def _initialize_default_store(registry: VectorStoreRegistry) -> None:
    """Register the default vector store based on VECTOR_DB_TYPE.

    Called once during application startup.  Keeps backward compatibility with
    the existing ``get_db_store()`` / ``get_db_client()`` functions.
    """
    from core.config.base import get_vector_database_settings

    db_settings = get_vector_database_settings()
    db_type = db_settings.VECTOR_DB_TYPE

    if db_type == "PGVECTOR":
        from stores.pgvector_db import pgvector_store

        registry.register("default", pgvector_store)
    elif db_type == "QDRANT":
        from stores.qdrant_db import qdrant_store

        registry.register("default", qdrant_store)
    elif db_type == "COSMOS":
        from stores.cosmos_db import cosmos_db_store

        registry.register("default", cosmos_db_store)
    elif db_type == "ORACLE":
        from stores.oracle import oracle_db_store

        registry.register("default", oracle_db_store)
    else:
        logger.warning(
            "Unknown VECTOR_DB_TYPE=%r — no default store registered", db_type
        )
