"""Admin scheduler routes (TaskIQ-backed).

HTTP contract preserved:
- POST /scheduler/create-job
- POST /scheduler/cancel-job

The legacy `GET /scheduler/pool-status` endpoint is removed — TaskIQ uses
its own connection pool; monitor via Grafana + `taskiq_messages` table stats.
"""

import logging

from litestar import Controller, post
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.admin_ops import cancel_job, create_or_update_job
from tasks.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


class SchedulerController(Controller):
    path = "/scheduler"
    tags = ["Admin / Scheduler"]

    @post("/create-job")
    async def create_job(self, data: JobDefinition, db_session: AsyncSession) -> dict:
        return await create_or_update_job(data, db_session)

    @post("/cancel-job")
    async def cancel_job(self, data: JobIdInput, db_session: AsyncSession) -> dict:
        return await cancel_job(data.job_id, db_session)
