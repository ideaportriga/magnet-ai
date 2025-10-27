from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import pandas as pd
from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body, Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.evaluation_sets.service import (
    EvaluationSetsService,
)

from .schemas import EvaluationSet, EvaluationSetCreate, EvaluationSetUpdate

if TYPE_CHECKING:
    pass


@dataclass
class FormData:
    json: str
    file: UploadFile | None = None


class EvaluationSetsController(Controller):
    """Evaluation Sets CRUD"""

    path = "/evaluation_sets"
    tags = ["Admin / Evaluation Sets"]

    dependencies = providers.create_service_dependencies(
        EvaluationSetsService,
        "evaluation_sets_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_evaluation_sets(
        self,
        evaluation_sets_service: EvaluationSetsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[EvaluationSet]:
        """List evaluation sets with pagination and filtering."""
        results, total = await evaluation_sets_service.list_and_count(*filters)
        return evaluation_sets_service.to_schema(
            results, total, filters=filters, schema_type=EvaluationSet
        )

    @post()
    async def create_evaluation_set(
        self, evaluation_sets_service: EvaluationSetsService, data: EvaluationSetCreate
    ) -> EvaluationSet:
        """Create a new evaluation set."""
        obj = await evaluation_sets_service.create(data)
        return evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)

    @post("/file")
    async def create_evaluation_set_from_file(
        self,
        evaluation_sets_service: EvaluationSetsService,
        data: Annotated[FormData, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> EvaluationSet:
        """Create a new evaluation set from file upload."""
        json_data = json.loads(data.json)
        evaluation_set_data = EvaluationSetCreate(**json_data)

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
                item = {
                    "user_input": user_input,
                    "expected_result": expected_result,
                }
                items.append(item)

            # Update the items in the data
            evaluation_set_data.items = items

        obj = await evaluation_sets_service.create(evaluation_set_data)
        return evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)

    @get("/code/{code:str}")
    async def get_evaluation_set_by_code(
        self, evaluation_sets_service: EvaluationSetsService, code: str
    ) -> EvaluationSet:
        """Get an evaluation set by its system_name."""
        obj = await evaluation_sets_service.get_one(system_name=code)
        return evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)

    @get("/{evaluation_set_id:uuid}")
    async def get_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to retrieve.",
        ),
    ) -> EvaluationSet:
        """Get an evaluation set by its ID."""
        obj = await evaluation_sets_service.get(evaluation_set_id)
        return evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)

    @patch("/{evaluation_set_id:uuid}")
    async def update_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        data: EvaluationSetUpdate,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to update.",
        ),
    ) -> EvaluationSet:
        """Update an evaluation set."""
        obj = await evaluation_sets_service.update(data, item_id=evaluation_set_id, auto_commit=True)
        return evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)

    @delete("/{evaluation_set_id:uuid}")
    async def delete_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to delete.",
        ),
    ) -> None:
        """Delete an evaluation set."""
        await evaluation_sets_service.delete(evaluation_set_id)
