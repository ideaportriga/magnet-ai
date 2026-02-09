from datetime import UTC, datetime
from functools import wraps
from logging import getLogger

from scheduler.types import JobDefinition, JobStatus, JobType
from scheduler.utils import update_job_status

logger = getLogger(__name__)


def with_progress_status(func):
    """Set status to PROCESSING before execution; ERROR on exception.

    For recurring jobs the status is set back to WAITING on completion
    (AsyncMQ's repeatable scheduler handles the next enqueue automatically).
    For one-time jobs the status is set to COMPLETED.
    """

    @wraps(func)
    async def wrapper(**kwargs):
        job_id = kwargs.get("job_id")
        try:
            if job_id:
                await update_job_status(job_id, JobStatus.PROCESSING)
            result = await func(**kwargs)
            # On success, update status
            if job_id:
                current_time = datetime.now(UTC).isoformat()
                job_definition = kwargs.get("job_definition")
                if job_definition:
                    jd = JobDefinition.model_validate(job_definition)
                    if jd.job_type == JobType.RECURRING:
                        await update_job_status(
                            job_id, JobStatus.WAITING, {"last_run": current_time}
                        )
                    else:
                        await update_job_status(
                            job_id, JobStatus.COMPLETED, {"last_run": current_time}
                        )
                else:
                    await update_job_status(
                        job_id, JobStatus.COMPLETED, {"last_run": current_time}
                    )
            return result
        except Exception as e:
            if job_id:
                try:
                    current_time = datetime.now(UTC).isoformat()
                    job_definition = kwargs.get("job_definition")
                    if job_definition:
                        jd = JobDefinition.model_validate(job_definition)
                        if jd.job_type == JobType.RECURRING:
                            await update_job_status(
                                job_id,
                                JobStatus.WAITING,
                                {"last_run": current_time, "error": str(e)},
                            )
                        else:
                            await update_job_status(
                                job_id,
                                JobStatus.ERROR,
                                {"last_run": current_time, "error": str(e)},
                            )
                    else:
                        await update_job_status(job_id, JobStatus.ERROR)
                except Exception as update_error:
                    logger.error(
                        f"Failed to update job status for job {job_id}: {str(update_error)}"
                    )
            raise

    return wrapper
