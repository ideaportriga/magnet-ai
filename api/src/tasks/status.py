"""`@with_job_status` — writes PROCESSING/COMPLETED/WAITING/ERROR into `jobs` table.

Replaces the legacy APScheduler event-listener machinery (`job_executed_listener`,
`job_error_listener`, etc.) and the `with_progress_status` decorator from
`scheduler/executors.py`.

Responsibilities:
- On enter: idempotency guard — if job already in a terminal state, skip (prevents
  duplicate execution on at-least-once redelivery).
- On enter: set PROCESSING + last_run.
- On success: for RECURRING set WAITING + compute next_run; for one-time set COMPLETED.
- On error: for RECURRING set WAITING + error text + next_run; for one-time set ERROR.
- Jobs without `job_id` (system cron tasks) bypass status tracking entirely.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import wraps
from logging import getLogger
from typing import Any, Awaitable, Callable
from uuid import UUID

from core.config.app import alchemy
from core.db.models.job import Job
from core.domain.jobs.schemas import JobUpdate
from core.domain.jobs.service import JobsService
from tasks.cron import compute_next_run, cron_config_to_expression
from tasks.types import CronConfig, JobStatus, JobType

logger = getLogger(__name__)

_TERMINAL_STATUSES = {
    JobStatus.COMPLETED.value,
    JobStatus.ERROR.value,
    JobStatus.CANCELED.value,
}


async def _load_job(job_id: str) -> Job | None:
    try:
        job_uuid = UUID(job_id)
    except (ValueError, TypeError):
        return None
    async with alchemy.get_session() as session:
        return await JobsService(session=session).get_one_or_none(id=job_uuid)


async def _update_job(job_id: str, **fields: Any) -> None:
    try:
        job_uuid = UUID(job_id)
    except (ValueError, TypeError):
        return
    try:
        async with alchemy.get_session() as session:
            await JobsService(session=session).update(
                JobUpdate(**fields), item_id=job_uuid, auto_commit=True
            )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to update job %s status: %s", job_id, exc)


def _coerce_definition(job_definition: Any) -> dict:
    # JSONB sometimes surfaces as a raw JSON string (e.g. when a connection
    # misses the asyncpg jsonb codec registration — observed inside taskiq
    # worker sessions). Parse defensively so the lifecycle decorator never
    # crashes on the type mismatch.
    if isinstance(job_definition, str):
        try:
            return json.loads(job_definition)
        except (ValueError, TypeError):
            return {}
    if isinstance(job_definition, dict):
        return job_definition
    return {}


def _is_recurring(job_definition: Any) -> bool:
    return _coerce_definition(job_definition).get("job_type") == JobType.RECURRING.value


def _next_run_for(job_definition: Any) -> datetime | None:
    job_definition = _coerce_definition(job_definition)
    if not _is_recurring(job_definition):
        return None
    cron_dict = job_definition.get("cron")
    if not cron_dict:
        return None
    try:
        cron = CronConfig.model_validate(cron_dict)
        expr = cron_config_to_expression(cron)
        timezone = job_definition.get("timezone") or "UTC"
        return compute_next_run(expr, timezone)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to compute next_run for recurring job: %s", exc)
        return None


def with_job_status(
    fn: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """Decorate a task body with `jobs.status` lifecycle updates."""

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        job_id = kwargs.get("job_id")

        # System cron tasks have no job row — execute directly.
        if not job_id:
            return await fn(*args, **kwargs)

        job = await _load_job(job_id)
        if job is None:
            # Job row deleted mid-flight: execute but don't write status.
            logger.info(
                "Task received job_id=%s but no row exists; running without status tracking",
                job_id,
            )
            return await fn(*args, **kwargs)

        # Idempotency guard: at-least-once redelivery should not re-execute
        # one-time tasks that already completed/errored/cancelled.
        if job.status in _TERMINAL_STATUSES:
            logger.info(
                "Task %s redelivered but already in terminal state %s — skipping",
                job_id,
                job.status,
            )
            return None

        definition = _coerce_definition(job.definition)
        is_recurring = _is_recurring(definition)

        await _update_job(
            job_id,
            status=JobStatus.PROCESSING.value,
            last_run=datetime.now(UTC),
        )

        try:
            result = await fn(*args, **kwargs)
        except Exception as exc:
            terminal = (
                JobStatus.WAITING.value if is_recurring else JobStatus.ERROR.value
            )
            await _update_job(
                job_id,
                status=terminal,
                next_run=_next_run_for(definition),
            )
            logger.error("Task %s failed: %s", job_id, exc)
            raise
        else:
            terminal = (
                JobStatus.WAITING.value if is_recurring else JobStatus.COMPLETED.value
            )
            await _update_job(
                job_id,
                status=terminal,
                next_run=_next_run_for(definition),
            )
            return result

    return wrapper
