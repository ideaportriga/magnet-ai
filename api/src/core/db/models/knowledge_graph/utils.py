import logging
from typing import Any
from uuid import UUID

from openai_model.utils import get_model_by_system_name

logger = logging.getLogger(__name__)


def graph_suffix(graph_id: UUID | str) -> str:
    """Return a safe table name suffix for a graph id."""
    s = str(graph_id)
    return s.replace("-", "_")


def docs_table_name(graph_id: UUID | str) -> str:
    """Per-graph documents table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_docs"


def docs_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph documents index prefix."""
    return f"idx_kg_{graph_suffix(graph_id)}_docs_"


def chunks_table_name(graph_id: UUID | str) -> str:
    """Per-graph chunks table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_chunks"


def chunks_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph chunks index prefix."""
    return f"idx_kg_{graph_suffix(graph_id)}_chunks_"


def entities_table_name(graph_id: UUID | str) -> str:
    """Per-graph extracted entities table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_entities"


def entities_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph extracted entities index prefix.

    Uses no trailing underscore so derived index names stay under PostgreSQL's
    63-character limit for UUID-based graph suffixes.
    """
    return f"idx_kg_{graph_suffix(graph_id)}_entities"


def edges_table_name(graph_id: UUID | str) -> str:
    """Per-graph edges table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_edges"


def edges_index_prefix(graph_id: UUID | str) -> str:
    """Per-graph edges index prefix."""
    return f"idx_kg_{graph_suffix(graph_id)}_edges"


def vec_table_name(graph_id: UUID | str, vec_size: int) -> str:
    """Per-graph vector table name, scoped to embedding dimension."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_{vec_size}_vec"


def vec_index_prefix(graph_id: UUID | str, vec_size: int) -> str:
    """Per-graph vector index prefix."""
    return f"idx_kg_{graph_suffix(graph_id)}_{vec_size}_vec"


def to_uuid(v: Any) -> UUID | None:
    if v is None:
        return None
    if isinstance(v, UUID):
        return v
    # Many queries cast UUID to text for JSON responses; accept that too.
    return UUID(str(v))


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
