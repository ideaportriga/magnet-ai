"""Housekeeping tasks: log retention cleanup, upload cleanup, token cleanup."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any

from services.observability import observability_context, observe
from tasks.broker import broker
from tasks.status import with_job_status

logger = getLogger(__name__)


@broker.task(task_name="cleanup_logs", timeout=1800)
@with_job_status
@observe(name="Cleanup logs", channel="Job")
async def cleanup_logs_task(
    *,
    job_id: str | None = None,
    retention_days: int = 30,
    cleanup_traces: bool = True,
    cleanup_metrics: bool = True,
    **_: Any,
) -> dict:
    """Delete old traces / metrics by retention window."""
    from sqlalchemy import delete

    from core.config.app import alchemy
    from core.db.models.metric.metric import Metric
    from core.db.models.trace.trace import Trace

    if retention_days < 1:
        raise ValueError(f"Invalid retention_days: {retention_days}")

    observability_context.update_current_trace(
        type="cleanup_logs",
        extra_data={
            "job_id": job_id,
            "params": {
                "retention_days": retention_days,
                "cleanup_traces": cleanup_traces,
                "cleanup_metrics": cleanup_metrics,
            },
        },
    )

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    deleted_traces = 0
    deleted_metrics = 0

    async with alchemy.get_session() as session:
        if cleanup_traces:
            result = await session.execute(
                delete(Trace).where(Trace.created_at < cutoff)
            )
            deleted_traces = result.rowcount or 0
        if cleanup_metrics:
            result = await session.execute(
                delete(Metric).where(Metric.created_at < cutoff)
            )
            deleted_metrics = result.rowcount or 0
        await session.commit()

    logger.info(
        "cleanup_logs job %s: deleted %d traces, %d metrics (retention=%dd)",
        job_id,
        deleted_traces,
        deleted_metrics,
        retention_days,
    )
    return {
        "deleted_traces": deleted_traces,
        "deleted_metrics": deleted_metrics,
        "retention_days": retention_days,
        "cutoff_date": cutoff.isoformat(),
    }


# ---------------------------------------------------------------------------
# System cron tasks (no job_id, invoked by LabelScheduleSource)
# ---------------------------------------------------------------------------


@broker.task(task_name="cleanup_old_uploads", timeout=600)
async def cleanup_old_uploads_task() -> None:
    """Remove knowledge-source upload files older than KS_UPLOAD_TTL_HOURS."""
    from services.file_cleanup import cleanup_old_uploads

    result = cleanup_old_uploads()
    if hasattr(result, "__await__"):
        await result


@broker.task(task_name="cleanup_note_taker_pending", timeout=600)
async def cleanup_note_taker_pending_task() -> None:
    """TTL cleanup for expired Teams note-taker speaker-mapping confirmations."""
    from services.agents.teams.note_taker_pending_store import cleanup_expired

    result = cleanup_expired()
    if hasattr(result, "__await__"):
        await result


@broker.task(task_name="cleanup_expired_refresh_tokens", timeout=600)
async def cleanup_expired_refresh_tokens_task() -> None:
    from services.users.refresh_token_service import cleanup_expired_tokens

    result = cleanup_expired_tokens()
    if hasattr(result, "__await__"):
        await result


@broker.task(task_name="recover_stuck_syncing_kg_sources", timeout=600)
async def recover_stuck_syncing_kg_sources_task() -> None:
    """Re-set KG sources stuck in 'syncing' state after a worker crash."""
    from services.knowledge_graph.sources.sync_recovery import (
        recover_stuck_syncing_sources,
    )

    result = recover_stuck_syncing_sources()
    if hasattr(result, "__await__"):
        await result
