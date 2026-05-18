"""Builtin recurring system tasks (replaces startup.py:_register_upload_cleanup_job).

Each task is registered with a static cron schedule via `LabelScheduleSource`.
They run without a `job_id`, so `@with_job_status` is a no-op for them (they
don't appear in the user-facing `jobs` table).

`recover_stuck_processing_jobs` is the only new task vs the legacy APScheduler
set — it closes the race between at-least-once redelivery and worker crashes
(see docs/TASKIQ_MIGRATION_PLAN.md §10.2).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from logging import getLogger

from sqlalchemy import text
from typing import Annotated

from taskiq import TaskiqDepends
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.broker import broker
from tasks.dependencies import get_db_session

logger = getLogger(__name__)


def _upload_cron() -> str:
    interval = int(os.environ.get("KS_UPLOAD_CLEANUP_INTERVAL_MINUTES", "60"))
    interval = max(1, min(interval, 59))
    return f"*/{interval} * * * *"


# -- 1. ks_upload_cleanup: every N minutes (default 60) --------------------
@broker.task(
    task_name="cleanup_old_uploads_cron",
    schedule=[{"cron": _upload_cron()}],
)
async def cleanup_old_uploads_cron() -> None:
    from tasks.definitions.housekeeping import cleanup_old_uploads_task

    await cleanup_old_uploads_task()


# -- 2. note_taker_pending_cleanup: every hour -----------------------------
@broker.task(
    task_name="cleanup_note_taker_pending_cron",
    schedule=[{"cron": "0 * * * *"}],
)
async def cleanup_note_taker_pending_cron() -> None:
    from tasks.definitions.housekeeping import cleanup_note_taker_pending_task

    await cleanup_note_taker_pending_task()


# -- 3. kg_sync_recovery: every 15 min -------------------------------------
@broker.task(
    task_name="recover_stuck_syncing_kg_sources_cron",
    schedule=[{"cron": "*/15 * * * *"}],
)
async def recover_stuck_syncing_kg_sources_cron() -> None:
    from tasks.definitions.housekeeping import recover_stuck_syncing_kg_sources_task

    await recover_stuck_syncing_kg_sources_task()


# -- 4. refresh_token_cleanup: every 6h ------------------------------------
@broker.task(
    task_name="cleanup_expired_refresh_tokens_cron",
    schedule=[{"cron": "0 */6 * * *"}],
)
async def cleanup_expired_refresh_tokens_cron() -> None:
    from tasks.definitions.housekeeping import cleanup_expired_refresh_tokens_task

    await cleanup_expired_refresh_tokens_task()


# -- 4b. recover stuck transcription jobs: every 15 min --------------------
@broker.task(
    task_name="recover_stuck_transcription_jobs_cron",
    schedule=[{"cron": "*/15 * * * *"}],
)
async def recover_stuck_transcription_jobs_cron() -> None:
    from tasks.definitions.housekeeping import recover_stuck_transcription_jobs_task

    await recover_stuck_transcription_jobs_task()


# -- 4c. cleanup teams_webhook_event rows: daily ---------------------------
@broker.task(
    task_name="cleanup_teams_webhook_events_cron",
    schedule=[{"cron": "0 3 * * *"}],
)
async def cleanup_teams_webhook_events_cron() -> None:
    from tasks.definitions.housekeeping import cleanup_teams_webhook_events_task

    await cleanup_teams_webhook_events_task()


# -- 4d. outbox retry for failed note-taker integrations: every 5 min ------
# Sweeper picks up `note_taker_integration_attempt` rows whose backoff
# slot is due (see integration_journal._RETRY_BACKOFF_SECONDS). At most
# 50 rows per tick — overflow is handled by the next cron beat.
@broker.task(
    task_name="retry_failed_note_taker_integrations_cron",
    schedule=[{"cron": "*/5 * * * *"}],
)
async def retry_failed_note_taker_integrations_cron() -> None:
    from tasks.definitions.housekeeping import (
        retry_failed_note_taker_integrations_task,
    )

    await retry_failed_note_taker_integrations_task()


# -- 5. recover stuck PROCESSING jobs: every 5 min -------------------------
@broker.task(
    task_name="recover_stuck_processing_jobs",
    schedule=[{"cron": "*/5 * * * *"}],
)
async def recover_stuck_processing_jobs_cron(
    session: Annotated[AsyncSession, TaskiqDepends(get_db_session)],
) -> None:
    """Move jobs that crashed mid-run (stuck in PROCESSING) to ERROR.

    A worker dying between task body completion and the COMPLETED status
    update leaves `jobs.status = 'Processing'` forever. We guard with max
    task timeout (30 min) + grace window.
    """
    from core.config.base import get_settings

    settings = get_settings()
    window = (
        settings.taskiq.TASKIQ_DEFAULT_TIMEOUT_SECONDS
        + settings.taskiq.TASKIQ_STUCK_PROCESSING_GRACE_SECONDS
    )
    cutoff = datetime.now(UTC) - timedelta(seconds=window)
    stmt = text(
        """
        UPDATE jobs
           SET status = 'Error'
         WHERE status = 'Processing'
           AND last_run IS NOT NULL
           AND last_run < :cutoff
        RETURNING id
        """
    )
    result = await session.execute(stmt, {"cutoff": cutoff})
    ids = [row[0] for row in result.all()]
    if ids:
        logger.warning(
            "Recovered %d stuck-PROCESSING jobs (worker crash suspected): %s",
            len(ids),
            ids,
        )
    await session.commit()
