import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from core.config.app import alchemy
from core.domain.jobs.schemas import JobUpdate
from core.domain.jobs.service import JobsService
from scheduler.types import JobStatus

logger = logging.getLogger(__name__)


async def update_job_status(
    job_id: str,
    status: JobStatus,
    additional_data: dict[str, Any] | None = None,
) -> None:
    """Update the status of a job in the database.

    Args:
        job_id: The ID of the job to update
        status: The new status for the job
        additional_data: Optional additional fields to update

    """
    try:
        async with alchemy.get_session() as session:
            service = JobsService(session=session)

            update_data: dict[str, Any] = {
                "status": status.value,
            }

            if additional_data:
                if "definition" in additional_data and isinstance(
                    additional_data["definition"], dict
                ):
                    update_data["definition"] = additional_data["definition"]
                if "next_run" in additional_data:
                    next_run_value = additional_data["next_run"]
                    if next_run_value is not None and isinstance(next_run_value, str):
                        try:
                            update_data["next_run"] = datetime.fromisoformat(
                                next_run_value.replace("Z", "+00:00")
                            )
                        except ValueError:
                            update_data["next_run"] = None
                    else:
                        update_data["next_run"] = next_run_value
                if "last_run" in additional_data:
                    last_run_value = additional_data["last_run"]
                    if last_run_value is not None and isinstance(last_run_value, str):
                        try:
                            update_data["last_run"] = datetime.fromisoformat(
                                last_run_value.replace("Z", "+00:00")
                            )
                        except ValueError:
                            update_data["last_run"] = None
                    else:
                        update_data["last_run"] = last_run_value

            # Validate and prepare update data
            # exclude_unset=True ensures only fields present in update_data are included
            job_update = JobUpdate.model_validate(update_data).model_dump(
                exclude_unset=True
            )

            await service.update(job_update, item_id=UUID(job_id), auto_commit=True)

        logger.debug(f"Updated job {job_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating job {job_id} status: {e!s}")


def format_next_run_time(job) -> str | None:
    """Format job's next run time to ISO format in UTC timezone.

    Args:
        job: The scheduler job object

    Returns:
        Formatted datetime string or None if no next run time

    """
    if not job or not job.next_run_time:
        return None

    utc_time = job.next_run_time.astimezone(UTC)
    return utc_time.isoformat()
