"""Job executor – enqueue / cancel jobs via AsyncMQ.

This module bridges the application's ``JobDefinition`` model with the
Async MQ multi-queue system.  Jobs are enqueued via ``queue.add()`` for
one-time execution and ``manager.add_repeatable()`` for recurring (cron)
jobs, using AsyncMQ's built-in repeatable scheduler.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.jobs.schemas import JobCreate, JobUpdate
from core.domain.jobs.service import JobsService
from scheduler.executors import RUN_CONFIG_HANDLERS
from scheduler.manager import (
    _build_cron_expr,
    add_repeatable,
    get_queue,
    get_queue_for_task_type,
    remove_repeatable_by_job_id,
)
from scheduler.types import JobDefinition, JobStatus, JobType
from scheduler.utils import update_job_status

logger = logging.getLogger(__name__)


def _cron_to_next_epoch(cron_config, timezone_str: str = "UTC") -> float:
    """Calculate the next run time (epoch seconds) from a ``CronConfig``."""
    cron_expr = _build_cron_expr(cron_config)
    now = datetime.now(UTC)
    cron_iter = croniter(cron_expr, now)
    next_dt = cron_iter.get_next(datetime)
    return next_dt.timestamp()


def _get_task_id(run_config_type) -> str:
    """Map a ``RunConfigurationType`` to the AsyncMQ task_id string."""
    handler = RUN_CONFIG_HANDLERS.get(run_config_type)
    if handler is None:
        raise ValueError(f"Unsupported run configuration type: {run_config_type}")
    return handler.task_id


async def create_job(
    data: JobDefinition,
    db_session: AsyncSession,
) -> dict:
    """Create (or update) a job record in the DB and enqueue it in AsyncMQ."""

    queue = get_queue()

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

    # Resolve the AsyncMQ task_id
    run_config_type = job_definition.run_configuration.type
    task_id = _get_task_id(run_config_type)

    # Determine target queue based on workload type
    queue_name = get_queue_for_task_type(run_config_type.value)
    queue = get_queue(queue_name)

    # Update job status in database
    await update_job_status(job_id, JobStatus.WAITING)

    # Build kwargs passed to the task function
    job_kwargs = {
        "job_id": job_id,
        "job_definition": job_definition.model_dump(mode="json"),
        "params": job_definition.run_configuration.params,
    }

    if job_definition.job_type == JobType.ONE_TIME_IMMEDIATE:
        # Run immediately
        await queue.add(task_id, kwargs=job_kwargs)
        logger.info(f"Enqueued immediate job {job_id}")

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

        # AsyncMQ uses ``delay`` in seconds from now
        delay_seconds = (scheduled_time - datetime.now(UTC)).total_seconds()
        await queue.add(task_id, kwargs=job_kwargs, delay=delay_seconds)
        logger.info(f"Enqueued scheduled job {job_id} for {scheduled_time}")

        await update_job_status(
            job_id, JobStatus.WAITING, {"next_run": scheduled_time.isoformat()}
        )

    elif job_definition.job_type == JobType.RECURRING:
        if not job_definition.cron:
            raise ValueError("Cron configuration is required for recurring jobs")

        cron_expr = _build_cron_expr(job_definition.cron)

        # Register with AsyncMQ's built-in repeatable scheduler on the
        # appropriate per-workload queue.
        await add_repeatable(
            task_id,
            cron=cron_expr,
            kwargs=job_kwargs,
            queue_name=queue_name,
        )

        # Calculate next run for display
        next_run_epoch = _cron_to_next_epoch(
            job_definition.cron, job_definition.timezone or "UTC"
        )
        next_run_iso = datetime.fromtimestamp(next_run_epoch, tz=UTC).isoformat()
        await update_job_status(job_id, JobStatus.WAITING, {"next_run": next_run_iso})
        logger.info(f"Registered recurring job {job_id}, next run at {next_run_iso}")

    return {
        "job_id": job_id,
        "status": JobStatus.WAITING,
        "job_type": job_definition.job_type,
    }


async def cancel_job(
    job_id: str,
    db_session: AsyncSession,
) -> dict:
    """Cancel a job – remove it from AsyncMQ and update DB status."""

    async with db_session as session:
        service = JobsService(session=session)
        job = await service.get_one_or_none(id=UUID(job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

    queue = get_queue()

    # For recurring jobs, remove from our custom repeatable scheduler
    try:
        job_definition = job.definition
        if isinstance(job_definition, dict):
            jd = JobDefinition.model_validate(job_definition)
            if jd.job_type == JobType.RECURRING:
                removed = await remove_repeatable_by_job_id(job_id)
                if removed:
                    logger.info(f"Removed repeatable for job {job_id}")
                else:
                    logger.warning(f"No repeatable found for job {job_id}")
    except Exception as e:
        logger.warning(f"Could not remove repeatable for job {job_id}: {e}")

    # Cancel any pending one-time job in AsyncMQ (best-effort)
    try:
        await queue.cancel_job(f"job:{job_id}")
        logger.info(f"Cancelled AsyncMQ job for {job_id}")
    except Exception as e:
        logger.warning(f"Could not cancel AsyncMQ job {job_id}: {e}")

    await update_job_status(job_id, JobStatus.CANCELED)
    return {"job_id": job_id, "status": JobStatus.CANCELED}
