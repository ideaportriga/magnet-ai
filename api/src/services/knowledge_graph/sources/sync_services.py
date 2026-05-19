from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource
from services.knowledge_graph.logging_settings import (
    resolve_tracing_level,
    tracing_level_to_export_method,
)
from services.observability import observability_context, observe
from services.observability.models import FeatureType
from utils.datetime_utils import utc_now_isoformat

logger = logging.getLogger(__name__)


async def _record_source_failure(source_id: UUID) -> None:
    """Persist a failure status on the source using a fresh session.

    The long-lived sync session may be invalid (asyncpg connection dropped
    mid-sync), so we cannot rely on it for the final status write.
    """

    try:
        async with alchemy.get_session() as recovery:
            await recovery.execute(
                update(KnowledgeGraphSource)
                .where(KnowledgeGraphSource.id == source_id)
                .values(
                    status="failed",
                    last_sync_at=utc_now_isoformat(),
                    sync_progress=None,
                )
            )
            await recovery.commit()
    except Exception:  # noqa: BLE001
        logger.warning("Failed to record sync failure for source %s", str(source_id))


async def sync_source_background(graph_id: UUID, source_id: UUID) -> None:
    """Run sync in background with its own database session.

    This method is called via asyncio.create_task() and should not raise exceptions
    to the caller. All errors are logged and stored in the source status via a
    fresh session, since the primary session may be invalidated by the failure.
    """

    try:
        async with alchemy.get_session() as db_session:
            await _sync_source_impl(db_session, graph_id, source_id)
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Background sync failed for graph {graph_id} source {source_id}: {e}",
            exc_info=True,
        )
        await _record_source_failure(source_id)


async def sync_source(
    db_session: AsyncSession, graph_id: UUID, source_id: UUID
) -> dict[str, Any]:
    """Synchronous sync method (used by scheduled jobs)."""
    return await _sync_source_impl(db_session, graph_id, source_id)


@observe(name="Sync knowledge graph", channel="production", source="production")
async def _sync_source_impl(
    db_session: AsyncSession, graph_id: UUID, source_id: UUID
) -> dict[str, Any]:
    """Internal implementation of sync logic."""
    result = await db_session.execute(
        select(KnowledgeGraphSource, KnowledgeGraph)
        .join(KnowledgeGraph, KnowledgeGraphSource.graph_id == KnowledgeGraph.id)
        .where(
            (KnowledgeGraphSource.id == source_id)
            & (KnowledgeGraphSource.graph_id == graph_id)
        )
    )
    row = result.first()
    if not row:
        raise NotFoundException("Source not found")

    source, graph = row

    observability_context.update_current_trace(
        name=graph.name, type=FeatureType.KNOWLEDGE_GRAPH.value
    )

    tracing_level = resolve_tracing_level(graph.settings, "sync_tracing_level")
    observability_context.update_current_config(
        span_export_method=tracing_level_to_export_method(tracing_level)
    )

    source.status = "syncing"
    sync_started_at = utc_now_isoformat()
    source.sync_progress = {
        "phase": "starting",
        "processed": 0,
        "total": 0,
        "current_document": None,
        "started_at": sync_started_at,
        "updated_at": sync_started_at,
    }
    await db_session.commit()

    try:
        if source.type == "sharepoint":
            from services.knowledge_graph.sources import SharePointDataSource

            summary = await SharePointDataSource(source).sync_source(db_session)
        elif source.type == "fluid_topics":
            from services.knowledge_graph.sources import FluidTopicsSource

            summary = await FluidTopicsSource(source).sync_source(db_session)
        elif source.type == "salesforce":
            from services.knowledge_graph.sources import SalesforceSource

            summary = await SalesforceSource(source).sync_source(db_session)
        elif source.type == "confluence":
            from services.knowledge_graph.sources import ConfluenceSource

            summary = await ConfluenceSource(source).sync_source(db_session)
        elif source.type == "web":
            from services.knowledge_graph.sources.web import WebDataSource

            summary = await WebDataSource(source).sync_source(db_session)
        else:
            raise NotFoundException(
                f"Sync for source type '{source.type}' is not implemented"
            )

        # `_finalize` (called inside `sync_source` on each concrete source)
        # already persists `status` and `last_sync_at` via a fresh session.
        return summary
    except Exception as e:  # noqa: BLE001
        # The long-lived session is likely invalidated; use a fresh one so
        # the failure is always recorded for both background and scheduled paths.
        await _record_source_failure(source_id)
        raise ClientException(f"Sync failed: {e}")
