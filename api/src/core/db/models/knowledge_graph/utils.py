import logging
import re
from functools import lru_cache
from typing import Any
from uuid import UUID

from sqlalchemy import MetaData, Table

from openai_model.utils import get_model_by_system_name

logger = logging.getLogger(__name__)

_SAFE_TABLE_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def _validate_table_name(name: str) -> str:
    """Validate that a dynamically generated table name is safe for SQL interpolation.

    Only lowercase alphanumeric and underscores are allowed (PostgreSQL identifier rules).
    Raises ValueError if the name contains unexpected characters.
    """
    if not _SAFE_TABLE_NAME_RE.match(name):
        raise ValueError(f"Unsafe dynamic table name: {name!r}")
    return name


def graph_suffix(graph_id: UUID | str) -> str:
    """Return a safe table name suffix for a graph id.

    Validates that graph_id is a proper UUID to prevent SQL injection
    via crafted graph identifiers.
    """
    uid = graph_id if isinstance(graph_id, UUID) else UUID(str(graph_id))
    return str(uid).replace("-", "_")


def docs_table_name(graph_id: UUID | str) -> str:
    """Per-graph documents table name."""
    return _validate_table_name(f"knowledge_graph_{graph_suffix(graph_id)}_docs")


def docs_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph documents index prefix."""
    return _validate_table_name(f"idx_kg_{graph_suffix(graph_id)}_docs_")


def chunks_table_name(graph_id: UUID | str) -> str:
    """Per-graph chunks table name."""
    return _validate_table_name(f"knowledge_graph_{graph_suffix(graph_id)}_chunks")


def chunks_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph chunks index prefix."""
    return _validate_table_name(f"idx_kg_{graph_suffix(graph_id)}_chunks_")


def entities_table_name(graph_id: UUID | str) -> str:
    """Per-graph extracted entities table name."""
    return _validate_table_name(f"knowledge_graph_{graph_suffix(graph_id)}_entities")


def entities_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph extracted entities index prefix.

    Uses no trailing underscore so derived index names stay under PostgreSQL's
    63-character limit for UUID-based graph suffixes.
    """
    return _validate_table_name(f"idx_kg_{graph_suffix(graph_id)}_entities")


def edges_table_name(graph_id: UUID | str) -> str:
    """Per-graph edges table name."""
    return _validate_table_name(f"knowledge_graph_{graph_suffix(graph_id)}_edges")


def edges_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph edges index prefix."""
    return _validate_table_name(f"idx_kg_{graph_suffix(graph_id)}_edges")


def to_uuid(v: Any) -> UUID | None:
    if v is None:
        return None
    if isinstance(v, UUID):
        return v
    # Many queries cast UUID to text for JSON responses; accept that too.
    return UUID(str(v))


# ---------------------------------------------------------------------------
# Cached Table object helpers
# ---------------------------------------------------------------------------
# Table() + MetaData() creation is pure but non-trivial. Caching avoids
# rebuilding them on every service call. The cache is keyed by
# (table_name, vector_size) so different vector sizes get separate entries.


@lru_cache(maxsize=256)
def get_cached_docs_table(docs_name: str, *, vector_size: int | None = None) -> Table:
    """Return a cached SQLAlchemy Table for a per-graph documents table."""
    from .knowledge_graph_document import knowledge_graph_document_table

    md = MetaData()
    return knowledge_graph_document_table(md, docs_name, vector_size=vector_size)


@lru_cache(maxsize=256)
def get_cached_chunks_table(
    chunks_name: str, *, docs_table: str, vector_size: int | None = None
) -> Table:
    """Return a cached SQLAlchemy Table for a per-graph chunks table."""
    from .knowledge_graph_chunk import knowledge_graph_chunk_table

    md = MetaData()
    return knowledge_graph_chunk_table(
        md, chunks_name, docs_table=docs_table, vector_size=vector_size
    )


@lru_cache(maxsize=256)
def get_cached_entities_table(table_name: str) -> Table:
    """Return a cached SQLAlchemy Table for a per-graph entities table."""
    from .knowledge_graph_entity import knowledge_graph_entity_table

    md = MetaData()
    return knowledge_graph_entity_table(md, table_name)


@lru_cache(maxsize=256)
def get_cached_edges_table(table_name: str) -> Table:
    """Return a cached SQLAlchemy Table for a per-graph edges table."""
    from .knowledge_graph_edge import knowledge_graph_edge_table

    md = MetaData()
    return knowledge_graph_edge_table(md, table_name)


async def resolve_vector_size_for_embedding_model(embedding_model: str | None) -> int:
    """Resolve vector size for a given embedding model, defaulting to 1536."""
    if not embedding_model:
        return 1536
    try:
        model_cfg = await get_model_by_system_name(embedding_model)
        cfgs = (model_cfg or {}).get("configs") or {}
        if isinstance(cfgs, dict):
            size = cfgs.get("vector_size")
            if isinstance(size, int) and size > 0:
                return size
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to resolve vector size for model %s: %s", embedding_model, exc
        )
    return 1536
