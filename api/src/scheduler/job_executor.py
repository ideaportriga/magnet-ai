"""Job executor – enqueue / cancel jobs via SAQ.

This module bridges the application's ``JobDefinition`` model with the SAQ
queue.  Instead of directly scheduling functions through APScheduler, jobs are
*enqueued* into the SAQ queue (optionally with a ``scheduled`` timestamp for
deferred execution).

Recurring jobs re-enqueue themselves after successful execution (handled
inside the executor functions in ``executors.py``).
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from croniter import croniter
from litestar_saq.config import TaskQueues
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.jobs.schemas import JobCreate, JobUpdate
from core.domain.jobs.service import JobsService
from scheduler.executors import RUN_CONFIG_HANDLERS
from scheduler.manager import get_queue
from scheduler.types import JobDefinition, JobStatus, JobType
from scheduler.utils import update_job_status

logger = logging.getLogger(__name__)


def _cron_to_next_epoch(cron_config, timezone_str: str = "UTC") -> float:
    """Calculate the next run time (epoch seconds) from a ``CronConfig``."""
    cron_params = {k: v for k, v in cron_config.model_dump().items() if v is not None}
    # Build a standard cron expression from the params (minute hour day month day_of_week)
    minute = str(cron_params.get("minute", "*"))
    hour = str(cron_params.get("hour", "*"))
    day = str(cron_params.get("day", "*"))
    month = str(cron_params.get("month", "*"))
    day_of_week = str(cron_params.get("day_of_week", "*"))

    cron_expr = f"{minute} {hour} {day} {month} {day_of_week}"
    now = datetime.now(UTC)
    cron_iter = croniter(cron_expr, now)
    next_dt = cron_iter.get_next(datetime)
    return next_dt.timestamp()


def _get_task_function_name(run_config_type) -> str:
    """Map a ``RunConfigurationType`` to the task function's ``__qualname__``."""
    handler = RUN_CONFIG_HANDLERS.get(run_config_type)
    if handler is None:
        raise ValueError(f"Unsupported run configuration type: {run_config_type}")
    return handler.__qualname__


async def create_job(
    task_queues: TaskQueues,
    data: JobDefinition,
    db_session: AsyncSession,
) -> dict:
    """Create (or update) a job record in the DB and enqueue it in SAQ."""

    queue = get_queue(task_queues)

    async with db_session as session:
        service = JobsService(session=session)

        if isinstance(data, dict) and "job_id" in data:
            job_id = data["job_id"]
            job_model = await service.get_one_or_none(id=UUID(job_id))
            if not job_model:
                raise ValueError(f"Job with ID {job_id} not found")
            job_definition = JobDefinition.model_validate(job_model.definition)
        elif isinstance(data, JobDefinition):
            run_config_type = data.run_configuration.type
            is_system = data.run_configuration.params.get("is_system", False)
            if is_system:
                from sqlalchemy import text

                result = await session.execute(
                    text("""
                        SELECT id FROM jobs
                        WHERE definition->'run_configuration'->>'type' = :run_config_type
                        AND definition->'run_configuration'->'params'->>'is_system' = 'true'
                    """),
                    {"run_config_type": run_config_type},
                )
                existing_system_job = result.first()
                if existing_system_job:
                    raise ValueError(
                        f"System job with type '{run_config_type}' and is_system=true already exists (job_id={existing_system_job[0]})",
                    )

            if hasattr(data, "job_id") and data.job_id:
                job_id = data.job_id
                existing_job = await service.get_one_or_none(id=UUID(job_id))
                if existing_job:
                    job_def_dict = data.model_dump()
                    job_def_dict.pop("job_id", None)
                    update_data = JobUpdate(
                        definition=job_def_dict,
                        status=JobStatus.CONFIGURATION.value,
                        next_run=None,
                        last_run=None,
                    )
                    await service.update(
                        update_data, item_id=UUID(job_id), auto_commit=True
                    )
                    logger.info(f"Updated existing job with ID {job_id}")
                else:
                    job_def_dict = data.model_dump()
                    job_def_dict.pop("job_id", None)
                    create_data = JobCreate(
                        definition=job_def_dict,
                        status=JobStatus.CONFIGURATION.value,
                        next_run=None,
                        last_run=None,
                    )
                    created_job = await service.create(create_data, auto_commit=True)
                    job_id = str(created_job.id)
                    logger.info(f"Created new job with ID {job_id}")
                job_definition = data
            else:
                create_data = JobCreate(
                    definition=data.model_dump(),
                    status=JobStatus.CONFIGURATION.value,
                    next_run=None,
                    last_run=None,
                )
                created_job = await service.create(create_data, auto_commit=True)
                job_id = str(created_job.id)
                job_definition = data
        else:
            raise ValueError(
                "Invalid input: expected JobDefinition or dictionary with job_id",
            )

    # Resolve the task function name for SAQ
    run_config_type = job_definition.run_configuration.type
    task_name = _get_task_function_name(run_config_type)

    # Update job status in database
    await update_job_status(job_id, JobStatus.WAITING)

    # Build kwargs passed to the task function
    job_kwargs = {
        "job_id": job_id,
        "job_definition": job_definition.model_dump(),
        "params": job_definition.run_configuration.params,
    }

    # Determine scheduled execution time (epoch seconds)
    scheduled: float | None = None

    if job_definition.job_type == JobType.ONE_TIME_IMMEDIATE:
        scheduled = None  # run immediately
        logger.info(f"Enqueuing immediate job {job_id}")

    elif job_definition.job_type == JobType.ONE_TIME_SCHEDULED:
        scheduled_time = job_definition.scheduled_start_time
        if scheduled_time is None:
            raise ValueError(
                "Scheduled start time is required for ONE_TIME_SCHEDULED jobs",
            )
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=UTC)
        else:
            scheduled_time = scheduled_time.astimezone(UTC)

        if scheduled_time <= datetime.now(UTC):
            raise ValueError("Scheduled start time must be in the future")

        scheduled = scheduled_time.timestamp()
        logger.info(f"Enqueuing scheduled job {job_id} for {scheduled_time}")

        # Record next_run
        await update_job_status(
            job_id, JobStatus.WAITING, {"next_run": scheduled_time.isoformat()}
        )

    elif job_definition.job_type == JobType.RECURRING:
        if not job_definition.cron:
            raise ValueError("Cron configuration is required for recurring jobs")

        next_run_epoch = _cron_to_next_epoch(
            job_definition.cron, job_definition.timezone or "UTC"
        )
        scheduled = next_run_epoch

        next_run_iso = datetime.fromtimestamp(next_run_epoch, tz=UTC).isoformat()
        await update_job_status(job_id, JobStatus.WAITING, {"next_run": next_run_iso})
        logger.info(f"Enqueuing recurring job {job_id}, next run at {next_run_iso}")

    # Enqueue in SAQ
    enqueue_kwargs: dict = {
        "key": f"job:{job_id}",
        **job_kwargs,
    }
    if scheduled is not None:
        enqueue_kwargs["scheduled"] = scheduled

    await queue.enqueue(task_name, **enqueue_kwargs)

    return {
        "job_id": job_id,
        "status": JobStatus.WAITING,
        "job_type": job_definition.job_type,
    }


async def cancel_job(
    task_queues: TaskQueues,
    job_id: str,
    db_session: AsyncSession,
) -> dict:
    """Cancel a job – abort it in SAQ if running and update DB status."""

    async with db_session as session:
        service = JobsService(session=session)
        job = await service.get_one_or_none(id=UUID(job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

    queue = get_queue(task_queues)

    # Attempt to abort in SAQ (best-effort)
    try:
        saq_job = await queue.job(f"job:{job_id}")
        if saq_job:
            await saq_job.abort("Canceled by user")
            logger.info(f"Aborted SAQ job for {job_id}")
    except Exception as e:
        logger.warning(f"Could not abort SAQ job {job_id}: {e}")

    await update_job_status(job_id, JobStatus.CANCELED)
    return {"job_id": job_id, "status": JobStatus.CANCELED}
