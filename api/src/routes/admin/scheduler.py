import logging

from litestar import Controller, get, post
from litestar_saq.config import TaskQueues
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.job_executor import cancel_job, create_job
from scheduler.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


class SchedulerController(Controller):
    path = "/scheduler"
    tags = ["Admin / Scheduler"]

    @post("/create-job")
    async def create_job(
        self,
        task_queues: TaskQueues,
        data: JobDefinition,
        db_session: AsyncSession,
    ) -> dict:
        return await create_job(task_queues, data, db_session)

    @post("/cancel-job")
    async def cancel_job(
        self, task_queues: TaskQueues, data: JobIdInput, db_session: AsyncSession
    ) -> dict:
        return await cancel_job(task_queues, data.job_id, db_session)

    @get("/queue-status")
    async def get_queue_status(self, task_queues: TaskQueues) -> dict:
        """Get current SAQ queue information."""
        from scheduler.manager import get_queue

        queue = get_queue(task_queues)
        info = await queue.info(jobs=True)
        return info
