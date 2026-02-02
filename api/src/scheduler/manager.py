import asyncio
from datetime import UTC, datetime
from logging import getLogger

import nest_asyncio
import pytz
from apscheduler.events import (
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    EVENT_JOB_MODIFIED,
    EVENT_JOB_REMOVED,
)
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from litestar import Request
from sqlalchemy import QueuePool

from core.config.base import get_database_settings, get_scheduler_settings
from scheduler.types import JobStatus
from scheduler.utils import format_next_run_time, update_job_status
from stores import get_db_client

logger = getLogger(__name__)
client = get_db_client()

# Global scheduler instance
_scheduler = None


def _run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        nest_asyncio.apply()
    return loop.run_until_complete(coro)


def get_global_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized yet")
    return _scheduler


def job_added_listener(event):
    """Listener for job added events"""
    scheduler = get_global_scheduler()
    job_id = event.job_id
    running_job = scheduler.get_job(job_id)

    next_run_time = format_next_run_time(running_job)
    _run_async(
        update_job_status(job_id, JobStatus.WAITING, {"next_run": next_run_time}),
    )
    logger.info(f"Job added: {job_id}")


def job_removed_listener(event):
    """Listener for job removed events"""
    logger.info(f"Job removed: {event.job_id}")


def job_modified_listener(event):
    """Listener for job modified events"""
    logger.info(f"Job modified: {event.job_id}")


def job_executed_listener(event):
    """Listener for job executed events"""
    try:
        job_id = event.job_id
        scheduler = get_global_scheduler()
        running_job = scheduler.get_job(job_id)

        next_run = format_next_run_time(running_job)
        current_time = datetime.now(UTC).isoformat()
        # WAITING if recurring job has next run, COMPLETED if one-time job finished
        status = JobStatus.WAITING if next_run else JobStatus.COMPLETED

        _run_async(
            update_job_status(
                job_id,
                status,
                {"last_run": current_time, "next_run": next_run},
            ),
        )
        logger.info(
            f"Job executed: {job_id}, scheduled run time: {event.scheduled_run_time}",
        )

    except Exception as e:
        logger.error(f"Error updating job status after execution: {e}")


def job_error_listener(event):
    """Listener for job error events"""
    try:
        job_id = event.job_id
        scheduler = get_global_scheduler()
        job = scheduler.get_job(job_id)

        current_time = datetime.now(UTC).isoformat()
        update_data = {
            "last_run": current_time,
            "error": str(event.exception),
        }

        # If job still has next_run_time despite the error, it might be recurring
        next_run = format_next_run_time(job)
        if next_run:
            update_data["next_run"] = next_run
            status = JobStatus.WAITING  # Will try again
        else:
            status = JobStatus.ERROR

        # Update the job in the database
        _run_async(update_job_status(job_id, status, update_data))

        logger.error(
            f"Job error: {job_id}, scheduled run time: {event.scheduled_run_time}",
        )
        logger.error(f"Exception: {event.exception}")

        # Log pool status when error occurs
        log_scheduler_pool_status()

        # Special handling for critical jobs
        if job_id.startswith("critical_"):
            logger.critical(f"Critical job failed: {job_id}")
    except Exception as e:
        logger.error(f"Error updating job status after error: {e}")
        # Try to log pool status even if job status update failed
        try:
            log_scheduler_pool_status()
        except Exception:
            pass


def job_missed_listener(event):
    """Listener for job missed events"""
    logger.warning(
        f"Job missed: {event.job_id}, scheduled run time: {event.scheduled_run_time}",
    )


async def create_scheduler() -> AsyncIOScheduler:
    """Creates and configures the application scheduler"""
    global _scheduler

    executors = {
        "thread": ProcessPoolExecutor(10),
        "default": AsyncIOExecutor(),
    }
    job_defaults = {
        "coalesce": True,
        "max_instances": 1,
    }
    scheduler = AsyncIOScheduler(
        executors=executors,
        job_defaults=job_defaults,
        timezone=pytz.UTC,
    )

    # Get database and scheduler settings from configuration
    db_settings = get_database_settings()
    scheduler_settings = get_scheduler_settings()

    # Get synchronous database URL for APScheduler
    sync_connection_string = scheduler_settings.get_scheduler_database_url(db_settings)

    if not sync_connection_string:
        logger.error("Database URL could not be determined from configuration")
        raise RuntimeError(
            "Database URL is required for scheduler. Check DATABASE_URL or DB_* environment variables."
        )

    # Get engine options from scheduler settings
    engine_options = scheduler_settings.get_engine_options()

    # Add database-specific connect_args
    if "postgresql" in sync_connection_string:
        engine_options["connect_args"] = {"application_name": "magnetui_scheduler"}

    logger.info(
        f"Configuring scheduler jobstore with pool_size={scheduler_settings.SCHEDULER_POOL_SIZE}, "
        f"max_overflow={scheduler_settings.SCHEDULER_MAX_POOL_OVERFLOW}, "
        f"pool_timeout={scheduler_settings.SCHEDULER_POOL_TIMEOUT}s, "
        f"pool_recycle={scheduler_settings.SCHEDULER_POOL_RECYCLE}s"
    )

    scheduler.add_jobstore(
        "sqlalchemy",
        "default",
        url=sync_connection_string,
        engine_options=engine_options,
    )

    # Add all event listeners
    scheduler.add_listener(job_added_listener, EVENT_JOB_ADDED)
    scheduler.add_listener(job_removed_listener, EVENT_JOB_REMOVED)
    scheduler.add_listener(job_modified_listener, EVENT_JOB_MODIFIED)
    scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
    scheduler.add_listener(job_missed_listener, EVENT_JOB_MISSED)

    logger.info("Starting scheduler...")
    scheduler.start()

    # Store the scheduler instance globally
    _scheduler = scheduler

    return scheduler


def get_scheduler_pool_info() -> dict:
    """Get information about the scheduler's connection pool"""
    global _scheduler
    if _scheduler is None:
        return {"error": "Scheduler not initialized"}

    try:
        # Get the SQLAlchemy jobstore
        jobstore = _scheduler._jobstores.get("default")
        if jobstore is not None and hasattr(jobstore, "engine"):
            pool: QueuePool = jobstore.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                # "invalid": pool.invalid(),
                "total_connections": pool.checkedout() + pool.checkedin(),
            }
        else:
            return {"error": "No SQLAlchemy engine found in jobstore"}
    except Exception as e:
        return {"error": f"Failed to get pool info: {e}"}


def log_scheduler_pool_status():
    """Log current scheduler connection pool status"""
    pool_info = get_scheduler_pool_info()
    if "error" in pool_info:
        logger.warning(f"Scheduler pool status: {pool_info['error']}")
    else:
        logger.info(
            f"Scheduler pool status - "
            f"Size: {pool_info['pool_size']}, "
            f"Checked out: {pool_info['checked_out']}, "
            f"Checked in: {pool_info['checked_in']}, "
            f"Overflow: {pool_info['overflow']}, "
            f"Invalid: {pool_info['invalid']}, "
            f"Total: {pool_info['total_connections']}"
        )


def get_scheduler(request: Request) -> AsyncIOScheduler:
    """Dependency provider function to get the scheduler instance from the app state"""
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise RuntimeError(
            "Scheduler is not available. Check if it was properly initialized during startup."
        )
    return scheduler
