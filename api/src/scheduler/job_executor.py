import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.jobs.schemas import JobCreate, JobUpdate
from core.domain.jobs.service import JobsService
from scheduler.executors import (
    RUN_CONFIG_HANDLERS,
)
from scheduler.types import JobDefinition, JobStatus, JobType
from scheduler.utils import update_job_status

logger = logging.getLogger(__name__)


async def create_job(
    scheduler: AsyncIOScheduler, data: JobDefinition, db_session: AsyncSession
) -> dict:
    # If data is a dictionary with job_id, fetch job from database
    async with db_session as session:
        service = JobsService(session=session)

        if isinstance(data, dict) and "job_id" in data:
            job_id = data["job_id"]
            # Fetch job configuration from SQLAlchemy
            job_model = await service.get_one_or_none(id=UUID(job_id))
            if not job_model:
                raise ValueError(f"Job with ID {job_id} not found")

            # Get job definition from model
            job_definition = JobDefinition.model_validate(job_model.definition)
        elif isinstance(data, JobDefinition):
            # --- Check for existing system job with same run_configuration.type ---
            run_config_type = data.run_configuration.type
            is_system = data.run_configuration.params.get("is_system", False)
            if is_system:
                # Check for existing system job through definition JSON field
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

            # Check if job_id is provided in the JobDefinition to update an existing job
            if hasattr(data, "job_id") and data.job_id:
                job_id = data.job_id
                # Check if job exists
                existing_job = await service.get_one_or_none(id=UUID(job_id))
                if existing_job:
                    # Update existing job with new definition
                    # Exclude job_id from the stored definition as it's not part of the actual configuration
                    job_def_dict = data.model_dump()
                    if "job_id" in job_def_dict:
                        del job_def_dict["job_id"]

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
                    # Create new job with specified ID
                    job_def_dict = data.model_dump()
                    if "job_id" in job_def_dict:
                        del job_def_dict["job_id"]

                    create_data = JobCreate(
                        definition=job_def_dict,
                        status=JobStatus.CONFIGURATION.value,
                        next_run=None,
                        last_run=None,
                    )
                    # Note: SQLAlchemy will auto-generate UUID, we can't specify custom ID easily
                    # If you need specific ID, you might need to handle this differently
                    created_job = await service.create(create_data, auto_commit=True)
                    job_id = str(created_job.id)
                    logger.info(f"Created new job with ID {job_id}")
                job_definition = data
            else:
                # Create new job with auto-generated ID
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

    # Get appropriate handler based on run configuration type
    run_config_type = job_definition.run_configuration.type
    if run_config_type not in RUN_CONFIG_HANDLERS:
        raise ValueError(f"Unsupported run configuration type: {run_config_type}")

    run_handler = RUN_CONFIG_HANDLERS[run_config_type]
    # func, params = run_handler(job_definition.run_configuration.params)

    # Update job status in database
    await update_job_status(job_id, JobStatus.WAITING)

    # Prepare job_kwargs with the full job object
    job_kwargs = {
        "job_id": job_id,
        "job_definition": job_definition.model_dump(),
        "params": job_definition.run_configuration.params,
    }

    # Configure and add the job to the scheduler
    if job_definition.job_type == JobType.ONE_TIME_IMMEDIATE:
        run_date = datetime.now(UTC) + timedelta(seconds=1)
        logger.info(f"Scheduling immediate job {job_id} to run at {run_date}")

        scheduler.add_job(
            func=run_handler,
            trigger="date",
            run_date=run_date,
            id=job_id,
            replace_existing=True,
            kwargs=job_kwargs,
            misfire_grace_time=60,  # Allow 60 seconds of misfire grace time
        )
    elif job_definition.job_type == JobType.ONE_TIME_SCHEDULED:
        # Ensure scheduled_start_time is timezone-aware
        scheduled_time = job_definition.scheduled_start_time
        if scheduled_time is None:
            raise ValueError(
                "Scheduled start time is required for ONE_TIME_SCHEDULED jobs",
            )

        # Explicitly ensure the time is in UTC
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=UTC)
        else:
            scheduled_time = scheduled_time.astimezone(UTC)

        # Validate the scheduled time is in the future
        if scheduled_time <= datetime.now(UTC):
            raise ValueError("Scheduled start time must be in the future")

        scheduler.add_job(
            func=run_handler,
            trigger="date",
            run_date=scheduled_time,
            id=job_id,
            replace_existing=True,
            kwargs=job_kwargs,
            misfire_grace_time=60,  # Allow 60 seconds of misfire grace time
        )
    elif job_definition.job_type == JobType.RECURRING:
        # For recurring jobs, extract cron parameters from the CronConfig object
        if not job_definition.cron:
            raise ValueError("Cron configuration is required for recurring jobs")
        # Extract non-None values from the CronConfig object
        cron_params = {
            k: v for k, v in job_definition.cron.model_dump().items() if v is not None
        }

        # Set timezone from job_definition (defaults to UTC via model validator)
        cron_params["timezone"] = pytz.timezone(job_definition.timezone)

        # Create the CronTrigger with the extracted parameters
        cron_trigger = CronTrigger(**cron_params)

        scheduler.add_job(
            func=run_handler,
            trigger=cron_trigger,
            id=job_id,
            replace_existing=True,
            kwargs=job_kwargs,
            misfire_grace_time=60,  # Allow 60 seconds of misfire grace time
        )
    return {
        "job_id": job_id,
        "status": JobStatus.WAITING,
        "job_type": job_definition.job_type,
    }


async def cancel_job(
    scheduler: AsyncIOScheduler, job_id: str, db_session: AsyncSession
) -> dict:
    # Check if job exists in the database
    async with db_session as session:
        service = JobsService(session=session)

        job = await service.get_one_or_none(id=UUID(job_id))
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        # Try to remove the job from the scheduler
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Successfully removed job {job_id} from scheduler")
        except Exception as e:
            logger.error(f"Error removing job {job_id} from scheduler: {e!s}")
            # If the job isn't in the scheduler, it might have completed or never been scheduled
            # We'll still update its status in the database

        # Update job status in database
        await update_job_status(job_id, JobStatus.CANCELED)

        return {"job_id": job_id, "status": JobStatus.CANCELED}
