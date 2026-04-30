"""Admin CRUD operations for user-facing jobs.

Replaces `src/scheduler/job_executor.py` (`create_job` / `cancel_job`).

The public HTTP contract on `/scheduler/create-job` and `/scheduler/cancel-job`
is preserved — UI is not touched. Internally we:
- Validate the JobDefinition + check is_system uniqueness.
- Upsert a row in `jobs` (user-facing status/next_run/last_run).
- For ONE_TIME_IMMEDIATE: enqueue via `task.kiq()`.
- For ONE_TIME_SCHEDULED: `schedule_by_time` on the AsyncpgScheduleSource.
- For RECURRING: `schedule_by_cron`, compute next_run via croniter.
- Store the TaskIQ schedule id on `jobs.taskiq_schedule_id` for cancel/cleanup.
"""

from __future__ import annotations

from datetime import UTC, datetime
from logging import getLogger
from typing import Any
from uuid import UUID

from litestar.exceptions import NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.job import Job as JobModel
from core.domain.jobs.schemas import JobCreate, JobUpdate
from core.domain.jobs.service import JobsService
from tasks.cron import compute_next_run, cron_config_to_expression
from tasks.definitions import DISPATCH_TABLE
from tasks.types import JobDefinition, JobStatus, JobType

logger = getLogger(__name__)


async def _ensure_no_duplicate_system_job(
    session: AsyncSession, run_config_type: str
) -> None:
    """Prevent two system-owned jobs of the same run_configuration type."""
    result = await session.execute(
        select(JobModel.id).where(
            JobModel.definition["run_configuration"]["type"].astext == run_config_type,
            JobModel.definition["run_configuration"]["params"]["is_system"].astext
            == "true",
        )
    )
    existing = result.first()
    if existing:
        raise ValueError(
            f"System job with type '{run_config_type}' and is_system=true already "
            f"exists (job_id={existing[0]})"
        )


async def _upsert_job_row(
    session: AsyncSession, data: JobDefinition
) -> tuple[str, JobDefinition]:
    """Create or update the user-facing `jobs` row from a JobDefinition.

    Returns (job_id, job_definition_to_use_for_kiq).
    """
    service = JobsService(session=session)

    if data.job_id:
        existing = await service.get_one_or_none(id=UUID(data.job_id))
        job_def = data.model_dump()
        job_def.pop("job_id", None)

        if existing:
            await service.update(
                JobUpdate(
                    definition=job_def,
                    status=JobStatus.CONFIGURATION.value,
                    next_run=None,
                    last_run=None,
                ),
                item_id=UUID(data.job_id),
                auto_commit=True,
            )
            return data.job_id, data
        else:
            created = await service.create(
                JobCreate(
                    definition=job_def,
                    status=JobStatus.CONFIGURATION.value,
                ),
                auto_commit=True,
            )
            return str(created.id), data
    else:
        created = await service.create(
            JobCreate(
                definition=data.model_dump(),
                status=JobStatus.CONFIGURATION.value,
            ),
            auto_commit=True,
        )
        return str(created.id), data


async def _finalize_job(
    session: AsyncSession,
    job_id: str,
    next_run: datetime | None,
    taskiq_schedule_id: str | None,
) -> None:
    service = JobsService(session=session)
    await service.update(
        JobUpdate(
            status=JobStatus.WAITING.value,
            next_run=next_run,
            taskiq_schedule_id=taskiq_schedule_id,
        ),
        item_id=UUID(job_id),
        auto_commit=True,
    )


async def create_or_update_job(
    data: JobDefinition, db_session: AsyncSession
) -> dict[str, Any]:
    run_config_type = data.run_configuration.type
    if run_config_type not in DISPATCH_TABLE:
        raise ValueError(f"Unsupported run_configuration type: {run_config_type}")

    if data.run_configuration.params.get("is_system") is True and not data.job_id:
        await _ensure_no_duplicate_system_job(db_session, run_config_type.value)

    job_id, defn = await _upsert_job_row(db_session, data)

    task = DISPATCH_TABLE[run_config_type]
    kwargs: dict[str, Any] = {**defn.run_configuration.params, "job_id": job_id}

    next_run: datetime | None = None
    schedule_id: str | None = None

    # Import schedule_source lazily so API processes don't connect to the broker
    # just by importing this module during route registration.
    from tasks import schedule_source

    # For scheduled/recurring jobs, obtain the schedule_id + next_run BEFORE the
    # status flip. ONE_TIME_IMMEDIATE gets nothing pre-kiq (schedule_id=None).
    if defn.job_type is JobType.ONE_TIME_SCHEDULED:
        scheduled = defn.scheduled_start_time
        if scheduled is None:
            raise ValueError("scheduled_start_time is required for ONE_TIME_SCHEDULED")
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=UTC)
        scheduled = scheduled.astimezone(UTC)
        if scheduled <= datetime.now(UTC):
            raise ValueError("Scheduled start time must be in the future")

        schedule = await task.schedule_by_time(schedule_source, scheduled, **kwargs)
        schedule_id = schedule.schedule_id
        next_run = scheduled

    elif defn.job_type is JobType.RECURRING:
        if defn.cron is None:
            raise ValueError("cron configuration is required for RECURRING jobs")
        expr = cron_config_to_expression(defn.cron)
        timezone = defn.timezone or "UTC"
        schedule = await task.schedule_by_cron(
            schedule_source, expr, cron_offset=timezone, **kwargs
        )
        schedule_id = schedule.schedule_id
        next_run = compute_next_run(expr, timezone)

    # CRITICAL: finalize status → Waiting BEFORE enqueuing the immediate task.
    # Otherwise there's a race where the worker picks up the message and writes
    # `Processing` → `Completed` before our deferred `Waiting` UPDATE lands,
    # leaving the job stuck in Waiting forever (the API's late UPDATE wins).
    await _finalize_job(db_session, job_id, next_run, schedule_id)

    if defn.job_type is JobType.ONE_TIME_IMMEDIATE:
        try:
            kicked = await task.kiq(**kwargs)
            logger.info(
                "Enqueued ONE_TIME_IMMEDIATE task for job %s: task_id=%s",
                job_id,
                kicked.task_id,
            )
        except Exception:
            logger.exception(
                "Failed to enqueue task for job %s (run_config=%s)",
                job_id,
                run_config_type.value,
            )
            raise

    logger.info(
        "Created/updated job %s (type=%s, run_config=%s)",
        job_id,
        defn.job_type.value,
        run_config_type.value,
    )
    return {
        "job_id": job_id,
        "status": JobStatus.WAITING.value,
        "job_type": defn.job_type.value,
    }


async def cancel_job(job_id: str, db_session: AsyncSession) -> dict[str, Any]:
    from tasks import schedule_source

    service = JobsService(session=db_session)
    job = await service.get_one_or_none(id=UUID(job_id))
    if job is None:
        raise NotFoundException(f"Job {job_id} not found")

    if job.taskiq_schedule_id:
        try:
            await schedule_source.delete_schedule(job.taskiq_schedule_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to delete schedule %s for job %s: %s",
                job.taskiq_schedule_id,
                job_id,
                exc,
            )

    await service.update(
        JobUpdate(status=JobStatus.CANCELED.value, taskiq_schedule_id=None),
        item_id=UUID(job_id),
        auto_commit=True,
    )
    logger.info("Cancelled job %s", job_id)
    return {"job_id": job_id, "status": JobStatus.CANCELED.value}
