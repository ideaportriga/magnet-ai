import io
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import pandas as pd
from bson import ObjectId
from litestar import Controller, Router, delete, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Body
from pydantic import BaseModel, Field

from services.evaluation.evaluation import (
    EvaluationSetConfig,
    EvaluationSetItem,
    create_evaluation_job,
    get_evaluation_job,
    list_evaluation_jobs,
)
from stores import get_db_client

from .create_entity_controller import create_entity_controller

client = get_db_client()


class CreateEvaluationRunRequest(BaseModel):
    evaluation_set: str
    iteration_count: int = Field(default=1, ge=0, le=5)
    evaluation_target_tools: list[str] | None = None
    evaluation_target_tools_variants: list[str] | None = None


class EvaluationJobsController(Controller):
    path = "/jobs"

    @post()
    async def create_job(self, data: CreateEvaluationRunRequest) -> dict:
        return await create_evaluation_job(
            evaluation_set=data.evaluation_set,
            iteration_count=data.iteration_count,
            evaluation_target_tools=data.evaluation_target_tools,
            evaluation_target_tools_variants=data.evaluation_target_tools_variants,
        )

    @get()
    async def list_jobs(self) -> list[dict]:
        return await list_evaluation_jobs()

    @get(
        "/{job_id:str}",
    )
    async def get_job(self, job_id: str) -> dict:
        evaluation_job = await get_evaluation_job(job_id)
        if not evaluation_job:
            raise NotFoundException()
        return evaluation_job

    @delete(
        "/{entity_id:str}",
    )
    async def delete_job(self, entity_id: str) -> None:
        if not ObjectId.is_valid(entity_id):
            raise ClientException("Invalid entity ID")

        result = await client.get_collection("evaluation_jobs").delete_one(
            {"_id": ObjectId(entity_id)},
        )
        if result.deleted_count == 0:
            raise ClientException("No record deleted")


EvaluationSetsBaseController = create_entity_controller(
    path_param="/sets",
    collection_name="evaluation_sets",
    model=EvaluationSetConfig,
)


@dataclass
class FormData:
    json: str
    file: UploadFile | None = None


class EvaluationSetsController(EvaluationSetsBaseController):
    @post(
        "/file",
    )
    async def create_with_file(
        self,
        data: Annotated[FormData, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> dict:
        json_data = json.loads(data.json)

        evaluation_set_config_dict = EvaluationSetConfig(**json_data).model_dump()

        file = data.file

        if file:
            file_content = await file.read()
            excel_data = pd.read_excel(
                io.BytesIO(file_content),
                header=None,
                dtype=str,
            ).fillna("")

            items = []
            for index, row in excel_data.iterrows():
                user_input = row.get(0, "")
                expected_result = row.get(1, "")
                item = EvaluationSetItem(
                    user_input=user_input,
                    expected_result=expected_result,
                )
                items.append(item.__dict__)

            evaluation_set_config_dict["items"] = items

        # Add metadata
        metadata = {"created_at": datetime.utcnow(), "modified_at": datetime.utcnow()}
        evaluation_set_config_dict["_metadata"] = metadata

        # Insert into database
        result = await client.get_collection("evaluation_sets").insert_one(
            evaluation_set_config_dict,
        )

        return {"inserted_id": str(result.inserted_id)}


evaluation_router = Router(
    path="/evaluation",
    tags=["evaluation"],
    route_handlers=[EvaluationJobsController, EvaluationSetsController],
)
