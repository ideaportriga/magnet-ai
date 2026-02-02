import fnmatch
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraph

from .models import ChunkerStrategy, ContentConfig, ContentReaderName

logger = logging.getLogger(__name__)


def get_default_content_configs() -> list[ContentConfig]:
    return [
        ContentConfig(
            name="PDF",
            enabled=True,
            glob_pattern="*.pdf",
            reader={"name": ContentReaderName.PDF, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.LLM,
                "options": {
                    # LLM and recursive have separate semantics
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_size": 18000,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "PDF_DOCUMENT_CHUNKING",
                    "chunk_title_pattern": "",
                },
            },
        ),
        ContentConfig(
            name="Default",
            enabled=True,
            glob_pattern="",
            reader={"name": ContentReaderName.PLAIN_TEXT, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.RECURSIVE,
                "options": {
                    "llm_batch_size": 15000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_size": 15000,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 15000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "chunk_title_pattern": "",
                },
            },
        ),
    ]


async def get_graph_settings(
    db_session: AsyncSession, graph_id: UUID
) -> dict[str, Any]:
    """Get graph settings."""
    result = await db_session.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    )
    graph = result.scalar_one_or_none()

    if not graph or not graph.settings:
        return {}

    return graph.settings


async def get_graph_embedding_model(
    db_session: AsyncSession, graph_id: UUID
) -> str | None:
    """Get embedding model configured for the graph."""
    settings = await get_graph_settings(db_session, graph_id)
    indexing_cfg = settings.get("indexing") or {}
    model = indexing_cfg.get("embedding_model")
    return model.strip() if isinstance(model, str) and model.strip() else None


async def _get_all_configs(
    db_session: AsyncSession, graph_id: UUID
) -> list[ContentConfig]:
    settings = await get_graph_settings(db_session, graph_id)

    if not settings or "chunking" not in settings:
        # Return defaults if no settings exist
        return get_default_content_configs()

    chunking_settings = settings.get("chunking", {})
    content_settings = chunking_settings.get("content_settings", [])

    if not content_settings:
        # Return defaults if no content_settings exist
        return get_default_content_configs()

    # Parse content settings into ContentConfig objects
    configs = []
    for config_dict in content_settings:
        try:
            configs.append(ContentConfig(**config_dict))
        except Exception as e:
            logger.error(f"Failed to parse content config: {e}")
            continue

    return configs if configs else get_default_content_configs()


async def get_content_config(
    db_session: AsyncSession,
    graph_id: UUID,
    filename: str,
    source_id: str | None = None,
    source_type: str | None = None,
) -> ContentConfig | None:
    """Get content config matching filename and optionally source_id/source_type.

    Matching uses AND logic:
    - glob_pattern must match (if specified)
    - source_ids must match (if specified), otherwise falls back to deprecated source_types (if specified)
    If neither source_ids nor source_types are set, it matches all sources.
    """
    configs = await _get_all_configs(db_session, graph_id)

    normalized_filename = (filename or "").strip().lower()

    for config in configs:
        if not config.enabled:
            continue

        # Check glob pattern match
        glob_pattern = (config.glob_pattern or "").strip()
        if glob_pattern and not fnmatch.fnmatch(
            normalized_filename, glob_pattern.lower()
        ):
            continue

        # Check source match (AND logic)
        # - Prefer matching by explicit source_ids
        # - Fall back to legacy source_types if source_ids is not set
        # - If neither is set, match all sources
        if config.source_ids and len(config.source_ids) > 0:
            if not source_id or str(source_id) not in config.source_ids:
                continue
        elif config.source_types and len(config.source_types) > 0:
            if not source_type or str(source_type) not in config.source_types:
                continue

        return config

    return None
