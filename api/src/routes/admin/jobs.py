from typing import Any

from litestar import post
from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from services.jobs.run_job import run_job
from stores import get_db_client

from .create_entity_controller import create_entity_controller

client = get_db_client()

JobsBaseController = create_entity_controller(
    path_param="/jobs",
    collection_name="jobs",
)


class CreateJobRunRequest(BaseModel):
    type: str
    config: Any
    result_entity: str | None = None
    iteration_count: int = Field(default=1, ge=0, le=5)


class JobsController(JobsBaseController):
    tags = ["jobs"]

    @post("/start", status_code=HTTP_200_OK)
    async def start_job(self, data: CreateJobRunRequest) -> dict:
        try:
            return await run_job(data)
        except Exception as e:
            raise ClientException(str(e))
