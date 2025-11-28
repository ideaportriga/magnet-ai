import fnmatch
import logging
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
            source_types=["upload", "sharepoint", "fluid_topics"],
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
            source_types=["upload", "sharepoint", "fluid_topics"],
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


async def _get_all_configs(
    db_session: AsyncSession, graph_id: UUID
) -> list[ContentConfig]:
    # Fetch graph settings
    result = await db_session.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    )
    graph = result.scalar_one_or_none()

    if not graph or not graph.settings or "chunking" not in graph.settings:
        # Return defaults if no settings exist
        return get_default_content_configs()

    chunking_settings = graph.settings.get("chunking", {})
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
    source_type: str | None = None,
) -> ContentConfig | None:
    """Get content config matching filename and optionally source_type.

    Matching uses AND logic: both glob_pattern AND source_types (if specified) must match.
    If source_types is None or empty in config, it matches all source types.
    """
    configs = await _get_all_configs(db_session, graph_id)

    for config in configs:
        if not config.enabled:
            continue

        # Check glob pattern match
        if not fnmatch.fnmatch(filename.lower(), config.glob_pattern.lower()):
            continue

        # Check source type match (AND logic)
        # If source_types is not specified or empty in config, it matches all source types
        if config.source_types and len(config.source_types) > 0:
            if not source_type or source_type not in config.source_types:
                continue

        return config

    return None
