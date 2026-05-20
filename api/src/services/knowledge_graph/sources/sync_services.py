from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphSource,
    docs_table_name,
)
from services.knowledge_graph.logging_settings import (
    resolve_tracing_level,
    tracing_level_to_export_method,
)
from services.observability import observability_context, observe
from services.observability.models import FeatureType
from utils.datetime_utils import utc_now_isoformat

logger = logging.getLogger(__name__)

# Registry of actively running source-sync tasks keyed by source_id.
# Holds the Task object itself (not a bool) so the event loop keeps a strong
# reference and cannot garbage-collect / silently cancel the task mid-run.
_active_sync_tasks: dict[UUID, asyncio.Task[Any]] = {}


def is_sync_task_active(source_id: UUID) -> bool:
    """Return True if a background sync task is currently running for this source."""
    task = _active_sync_tasks.get(source_id)
    return task is not None and not task.done()


async def _record_source_interrupted(source_id: UUID) -> None:
    """Persist an 'interrupted' status on the source using a fresh session.

    Used when the sync task was cancelled (shutdown drain, GC, restart) and the
    primary session is likely invalidated. Best-effort: failures are logged
    but not raised.
    """
    try:
        async with alchemy.get_session() as recovery:
            await recovery.execute(
                update(KnowledgeGraphSource)
                .where(KnowledgeGraphSource.id == source_id)
                .values(
                    status="interrupted",
                    last_sync_at=utc_now_isoformat(),
                    sync_progress=None,
                )
            )
            await recovery.commit()
    except Exception:  # noqa: BLE001
        logger.warning(
            "Failed to record interrupted status for source %s", str(source_id)
        )


def log_sync_outcome(source_id: UUID):
    """Return a Task done-callback that logs the final outcome.

    Catches the case where the task is cancelled by the GC or otherwise dies
    without going through the wrapper's except blocks — guarantees at least one
    log line so a "silent death" is never silent.
    """

    def _cb(task: asyncio.Task[Any]) -> None:
        _active_sync_tasks.pop(source_id, None)
        try:
            if task.cancelled():
                logger.error(
                    "Source sync task CANCELLED for source %s (likely GC, "
                    "shutdown, or external cancel)",
                    source_id,
                )
                return
            exc = task.exception()
            if exc is not None:
                logger.error(
                    "Source sync task FAILED for source %s",
                    source_id,
                    exc_info=exc,
                )
            else:
                logger.info(
                    "Source sync task finished cleanly for source %s",
                    source_id,
                )
        except asyncio.CancelledError:
            logger.error(
                "Source sync task CANCELLED for source %s (during outcome check)",
                source_id,
            )
        except Exception:
            logger.error(
                "Error inspecting source sync task outcome for source %s",
                source_id,
                exc_info=True,
            )

    return _cb


async def reconcile_stale_source_syncs() -> int:
    """Mark orphan 'syncing' sources as 'interrupted' on process startup.

    Called once at startup. Any source whose status is still 'syncing' must be
    stale — no in-process task can possibly own it because the process just
    started. Also marks any 'processing' documents belonging to those sources
    as 'failed' so per-source pipeline-strip stats no longer show stale running
    counts. Returns the number of source rows updated.
    """
    stale_sources: list[tuple[Any, Any]] = []
    updated = 0
    try:
        async with alchemy.get_session() as db_session:
            fetch_res = await db_session.execute(
                select(KnowledgeGraphSource.id, KnowledgeGraphSource.graph_id).where(
                    KnowledgeGraphSource.status == "syncing"
                )
            )
            stale_sources = [(row[0], row[1]) for row in fetch_res.all()]

            if not stale_sources:
                return 0

            all_source_ids = [row[0] for row in stale_sources]
            upd_res = await db_session.execute(
                update(KnowledgeGraphSource)
                .where(KnowledgeGraphSource.id.in_(all_source_ids))
                .values(
                    status="interrupted",
                    last_sync_at=utc_now_isoformat(),
                    sync_progress=None,
                )
            )
            await db_session.commit()
            updated = int(upd_res.rowcount or 0)
            if updated:
                logger.warning(
                    "Reconciled %d stale source sync row(s) to 'interrupted'",
                    updated,
                )
    except Exception:
        logger.error("Failed to reconcile stale source syncs on startup", exc_info=True)
        return 0

    # Best-effort: mark in-flight documents as 'failed' so pipeline-strip stats
    # no longer show stale sync_running counts after reconciliation.
    by_graph: dict[Any, list[Any]] = {}
    for source_id, graph_id in stale_sources:
        by_graph.setdefault(graph_id, []).append(source_id)

    for graph_id, source_ids in by_graph.items():
        try:
            async with alchemy.get_session() as doc_session:
                await doc_session.execute(
                    text(
                        f"UPDATE {docs_table_name(graph_id)} "  # noqa: S608
                        f"SET status = 'failed', updated_at = CURRENT_TIMESTAMP "
                        f"WHERE source_id = ANY(CAST(:source_ids AS uuid[])) "
                        f"AND status = 'processing'"
                    ),
                    {"source_ids": [str(sid) for sid in source_ids]},
                )
                await doc_session.commit()
        except Exception:
            logger.warning(
                "Failed to reconcile processing documents for graph %s on startup",
                graph_id,
                exc_info=True,
            )

    return updated


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


async def sync_source_background(
    graph_id: UUID, source_id: UUID, *, from_scratch: bool = False
) -> None:
    """Run sync in background with its own database session.

    This method is called via asyncio.create_task() and should not raise exceptions
    to the caller. All errors are logged and stored in the source status via a
    fresh session, since the primary session may be invalidated by the failure.
    """

    try:
        async with alchemy.get_session() as db_session:
            await _sync_source_impl(
                db_session, graph_id, source_id, from_scratch=from_scratch
            )
    except asyncio.CancelledError:
        logger.warning(
            "Background sync cancelled for graph %s source %s — marking as interrupted",
            graph_id,
            source_id,
        )
        await _record_source_interrupted(source_id)
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Background sync failed for graph {graph_id} source {source_id}: {e}",
            exc_info=True,
        )
        await _record_source_failure(source_id)


async def sync_source(
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
    *,
    from_scratch: bool = False,
) -> dict[str, Any]:
    """Synchronous sync method (used by scheduled jobs)."""
    return await _sync_source_impl(
        db_session, graph_id, source_id, from_scratch=from_scratch
    )


@observe(name="Sync knowledge graph", channel="production", source="production")
async def _sync_source_impl(
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
    *,
    from_scratch: bool = False,
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

            summary = await SharePointDataSource(source).sync_source(
                db_session, from_scratch=from_scratch
            )
        elif source.type == "fluid_topics":
            from services.knowledge_graph.sources import FluidTopicsSource

            summary = await FluidTopicsSource(source).sync_source(
                db_session, from_scratch=from_scratch
            )
        elif source.type == "salesforce":
            from services.knowledge_graph.sources import SalesforceSource

            summary = await SalesforceSource(source).sync_source(
                db_session, from_scratch=from_scratch
            )
        elif source.type == "confluence":
            from services.knowledge_graph.sources import ConfluenceSource

            summary = await ConfluenceSource(source).sync_source(
                db_session, from_scratch=from_scratch
            )
        elif source.type == "web":
            from services.knowledge_graph.sources.web import WebDataSource

            summary = await WebDataSource(source).sync_source(
                db_session, from_scratch=from_scratch
            )
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
