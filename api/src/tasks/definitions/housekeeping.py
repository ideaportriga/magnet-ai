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


@broker.task(task_name="recover_stuck_transcription_jobs", timeout=600)
async def recover_stuck_transcription_jobs_task() -> None:
    """Re-check transcription rows stuck in `running`/`started` for >1h.

    The note-taker pipeline polls the STT provider in-process. If the
    worker dies mid-poll the row stays `running` forever — the user
    never gets a summary and `_RUNNING` doesn't repopulate after
    restart. This sweep asks the STT service for the real status and
    either resumes the pipeline (transient row stuck on a long job) or
    marks the row failed so monitors can alert.

    See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-2.
    """
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select, update

    from core.db.models.transcription.transcription import Transcription
    from core.db.session import async_session_maker

    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    async with async_session_maker() as session:
        result = await session.execute(
            select(Transcription.file_id, Transcription.id).where(
                Transcription.status.in_(["running", "started"]),
                Transcription.updated_at < cutoff,
            )
        )
        rows = result.all()

    if not rows:
        return

    logger.warning(
        "recover_stuck_transcription_jobs: re-checking %d row(s) stuck >1h", len(rows)
    )

    # Late import — speech_to_text may not be ready in every entry-point.
    from speech_to_text.transcription import service as transcription_service

    for file_id, row_id in rows:
        live_status: str | None = None
        try:
            live_status = await transcription_service.get_status(file_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "recover_stuck_transcription_jobs: get_status(%s) failed: %s",
                file_id,
                exc,
            )

        async with async_session_maker() as session:
            if live_status in {"completed", "transcribed", "diarized"}:
                # The provider says it's done — the row will be picked up
                # by anyone polling it. Nothing to do; log for visibility.
                logger.info(
                    "recover_stuck_transcription_jobs: %s actually %s, leaving row alone",
                    file_id,
                    live_status,
                )
                continue

            new_status = "failed"
            error = (
                f"recovered: worker stale, last live status={live_status or 'unknown'}"
            )
            await session.execute(
                update(Transcription)
                .where(Transcription.id == row_id)
                .values(status=new_status, error=error)
            )
            await session.commit()
            logger.warning(
                "recover_stuck_transcription_jobs: marked %s as failed (live=%s)",
                file_id,
                live_status,
            )


# Retention for `teams_webhook_event` deduplication / staging rows.
# Long enough that operators can correlate recent incidents against the
# raw notification payload, short enough that the table doesn't grow
# unboundedly. See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-1.
_TEAMS_WEBHOOK_EVENT_RETENTION_DAYS = 7


@broker.task(task_name="cleanup_teams_webhook_events", timeout=600)
async def cleanup_teams_webhook_events_task() -> None:
    """Delete `teams_webhook_event` rows older than the retention window.

    The table is the dedup boundary for Microsoft Graph at-least-once
    delivery — rows past the retention window are no longer useful (a
    Graph redelivery that far after the original would not be matched
    against by the upstream pipeline anyway).
    """
    from sqlalchemy import delete

    from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent
    from core.db.session import async_session_maker

    cutoff = datetime.now(UTC) - timedelta(days=_TEAMS_WEBHOOK_EVENT_RETENTION_DAYS)
    async with async_session_maker() as session:
        result = await session.execute(
            delete(TeamsWebhookEvent).where(TeamsWebhookEvent.received_at < cutoff)
        )
        await session.commit()
    deleted = result.rowcount or 0
    if deleted:
        logger.info(
            "cleanup_teams_webhook_events: deleted %d row(s) older than %dd",
            deleted,
            _TEAMS_WEBHOOK_EVENT_RETENTION_DAYS,
        )


# Outbox retry sweeper for failed note-taker integration publishes. The
# sweeper only resurrects rows that the journal explicitly armed for
# retry (retry_payload + next_retry_at), and only those whose backoff
# slot is due. Re-enqueueing dispatches by `integration_kind` to the
# matching `*_bg_task` so the worker can replay the publish.
# See NOTE_TAKER_REVISION_PLAN.md §3.3 P2-a.
@broker.task(task_name="retry_failed_note_taker_integrations", timeout=600)
async def retry_failed_note_taker_integrations_task() -> int:
    """Re-enqueue failed note-taker integration publishes whose backoff is due.

    Returns the number of attempts re-enqueued (for tests / metrics).
    Idempotent — concurrent sweepers won't double-fire because we mark
    `next_retry_at = NULL` inside the same transaction that selects the
    row, so a second sweeper sees the row as no-longer-ready.
    """
    from sqlalchemy import select, update

    from core.db.models.teams.note_taker_integration_attempt import (
        NoteTakerIntegrationAttempt,
    )
    from core.db.session import async_session_maker
    from services.agents.teams.integration_journal import RETRY_MAX_ATTEMPTS

    requeued = 0
    async with async_session_maker() as session:
        now = datetime.now(UTC)
        # Pull a bounded batch so a single sweeper run can't get stuck
        # behind hundreds of failed rows. The next cron tick handles the rest.
        batch_size = 50
        rows = (
            (
                await session.execute(
                    select(NoteTakerIntegrationAttempt)
                    .where(
                        NoteTakerIntegrationAttempt.status == "failed",
                        NoteTakerIntegrationAttempt.retry_payload.is_not(None),
                        NoteTakerIntegrationAttempt.next_retry_at.is_not(None),
                        NoteTakerIntegrationAttempt.next_retry_at <= now,
                        NoteTakerIntegrationAttempt.attempt_count < RETRY_MAX_ATTEMPTS,
                    )
                    .order_by(NoteTakerIntegrationAttempt.next_retry_at.asc())
                    .limit(batch_size)
                )
            )
            .scalars()
            .all()
        )

        if not rows:
            return 0

        # Claim every row in this batch in one statement so a parallel
        # sweeper picks none of them up.
        ids = [r.id for r in rows]
        await session.execute(
            update(NoteTakerIntegrationAttempt)
            .where(NoteTakerIntegrationAttempt.id.in_(ids))
            .values(next_retry_at=None)
        )
        await session.commit()

    from services.agents.teams.notetaker_metrics import (
        record_integration_retry_attempt,
    )

    # Rows whose kiq() failed need their next_retry_at restored so a
    # later sweeper picks them up again. We collect those ids and update
    # in one round-trip at the end.
    failed_ids: list = []
    no_replay_ids: list = []

    for row in rows:
        payload = row.retry_payload or {}
        kind = row.integration_kind
        try:
            if kind == "knowledge_graph":
                from tasks.definitions import note_taker_kg_ingest_bg_task

                await note_taker_kg_ingest_bg_task.kiq(**payload)
            elif kind == "salesforce":
                from tasks.definitions import note_taker_salesforce_publish_bg_task

                await note_taker_salesforce_publish_bg_task.kiq(**payload)
            elif kind == "confluence":
                from tasks.definitions import note_taker_confluence_publish_bg_task

                await note_taker_confluence_publish_bg_task.kiq(**payload)
            else:
                # Unknown integration_kind — defensive. Should never hit
                # given the journal only writes the three known kinds.
                logger.warning(
                    "retry_failed_note_taker_integrations: no replay task "
                    "for kind=%s, job_id=%s (id=%s) — manual retry required",
                    kind,
                    row.job_id,
                    row.id,
                )
                no_replay_ids.append(row.id)
                record_integration_retry_attempt(
                    integration=kind, outcome="no_replay_task"
                )
                continue
            requeued += 1
            record_integration_retry_attempt(integration=kind, outcome="requeued")
        except Exception:
            logger.exception(
                "retry_failed_note_taker_integrations: replay kiq failed "
                "for kind=%s, job_id=%s (id=%s)",
                kind,
                row.job_id,
                row.id,
            )
            failed_ids.append(row.id)
            record_integration_retry_attempt(integration=kind, outcome="kiq_failed")

    # Re-arm rows whose kiq() failed: short fallback (5 min) so a later
    # sweeper retries once the broker is healthy. Without this the row
    # sits next_retry_at=NULL forever (the claim-update we did upfront
    # cleared it). See NOTE_TAKER_REVISION_PLAN.md §3.3 P2-a follow-up.
    if failed_ids:
        from sqlalchemy import update

        async with async_session_maker() as session:
            await session.execute(
                update(NoteTakerIntegrationAttempt)
                .where(NoteTakerIntegrationAttempt.id.in_(failed_ids))
                .values(next_retry_at=datetime.now(UTC) + timedelta(minutes=5))
            )
            await session.commit()

    if requeued or failed_ids or no_replay_ids:
        logger.info(
            "retry_failed_note_taker_integrations: requeued=%d kiq_failed=%d "
            "no_replay=%d",
            requeued,
            len(failed_ids),
            len(no_replay_ids),
        )
    return requeued
