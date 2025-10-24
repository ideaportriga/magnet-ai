import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from litestar import Controller, get, post
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.job_executor import cancel_job, create_job
from scheduler.manager import get_scheduler_pool_info, log_scheduler_pool_status
from scheduler.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


class SchedulerController(Controller):
    path = "/scheduler"
    tags = ["scheduler"]

    @post("/create-job")
    async def create_job(
        self,
        scheduler: AsyncIOScheduler,
        data: JobDefinition,
        db_session: AsyncSession,
    ) -> dict:
        return await create_job(scheduler, data, db_session)

    @post("/cancel-job")
    async def cancel_job(
        self, scheduler: AsyncIOScheduler, data: JobIdInput, db_session: AsyncSession
    ) -> dict:
        return await cancel_job(scheduler, data.job_id, db_session)

    @get("/pool-status")
    async def get_pool_status(self) -> dict:
        """Get current scheduler connection pool status"""
        pool_info = get_scheduler_pool_info()
        log_scheduler_pool_status()  # Also log to console
        return pool_info
