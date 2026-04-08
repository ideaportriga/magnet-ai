from __future__ import annotations

from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource
from services.knowledge_graph.models import KnowledgeGraphTracingLevel
from services.observability import observability_context, observe
from services.observability.models import FeatureType, SpanExportMethod
from utils.datetime_utils import utc_now_isoformat


async def sync_source_background(graph_id: UUID, source_id: UUID) -> None:
    """Run sync in background with its own database session.

    This method is called via asyncio.create_task() and should not raise exceptions
    to the caller. All errors are logged and stored in the source status.
    """

    try:
        async with alchemy.get_session() as db_session:
            await _sync_source_impl(db_session, graph_id, source_id)
    except Exception as e:  # noqa: BLE001
        # Log the error but don't raise - this is running in background
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Background sync failed for graph {graph_id} source {source_id}: {e}",
            exc_info=True,
        )


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

    logging_cfg = (graph.settings or {}).get("logging") or {}
    tracing_level = (
        logging_cfg.get("tracing_level") or KnowledgeGraphTracingLevel.TOTALS_ONLY
    )
    if tracing_level == KnowledgeGraphTracingLevel.OFF:
        span_export_method: SpanExportMethod | None = SpanExportMethod.IGNORE
    elif tracing_level == KnowledgeGraphTracingLevel.FULL:
        span_export_method = None
    else:
        span_export_method = SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
    observability_context.update_current_config(span_export_method=span_export_method)

    source.status = "syncing"
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

        # Type-specific sync should set final status; update last_sync_at for visibility
        source.last_sync_at = utc_now_isoformat()
        await db_session.commit()
        return summary
    except Exception as e:  # noqa: BLE001
        source.status = "failed"
        if hasattr(source, "status_message"):
            setattr(source, "status_message", str(e))
        await db_session.commit()
        raise ClientException(f"Sync failed: {e}")
