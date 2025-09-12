from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from pydantic import BaseModel

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.evaluations.service import EvaluationsService

from .schemas import Evaluation, EvaluationCreate, EvaluationUpdate


class ScoreUpdateRequest(BaseModel):
    score: float
    score_comment: str | None = None


if TYPE_CHECKING:
    pass


class EvaluationsController(Controller):
    """Evaluations CRUD"""

    path = "/sql_evaluations"
    tags = ["sql_Evaluations"]

    dependencies = providers.create_service_dependencies(
        EvaluationsService,
        "evaluations_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "job_id",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @patch("/{evaluation_id:uuid}/result/{result_id:str}/score")
    async def update_result_score(
        self,
        evaluations_service: EvaluationsService,
        data: ScoreUpdateRequest,
        evaluation_id: UUID = Parameter(title="Evaluation ID"),
        result_id: str = Parameter(title="Result ID"),
        db_session: Annotated[Any, Dependency] = None,
    ) -> dict:
        updated = await evaluations_service.update_result_score(
            db_session=db_session,
            evaluation_id=str(evaluation_id),
            result_id=result_id,
            score=data.score,
            score_comment=data.score_comment,
        )
        return {"success": updated}

    @get()
    async def list_evaluations(
        self,
        evaluations_service: EvaluationsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Evaluation]:
        """List evaluations with pagination and filtering."""
        results, total = await evaluations_service.list_and_count(*filters)
        return evaluations_service.to_schema(
            results, total, filters=filters, schema_type=Evaluation
        )

    @post()
    async def create_evaluation(
        self, evaluations_service: EvaluationsService, data: EvaluationCreate
    ) -> Evaluation:
        """Create a new evaluation."""
        obj = await evaluations_service.create(data)
        return evaluations_service.to_schema(obj, schema_type=Evaluation)

    @get("/job/{job_id:str}")
    async def get_evaluations_by_job_id(
        self, evaluations_service: EvaluationsService, job_id: str
    ) -> list[Evaluation]:
        """Get evaluations by job ID."""
        objs = await evaluations_service.list(job_id=job_id)
        return [
            evaluations_service.to_schema(obj, schema_type=Evaluation) for obj in objs
        ]

    @get("/status/{status:str}")
    async def get_evaluations_by_status(
        self, evaluations_service: EvaluationsService, status: str
    ) -> list[Evaluation]:
        """Get evaluations by status."""
        objs = await evaluations_service.list(status=status)
        return [
            evaluations_service.to_schema(obj, schema_type=Evaluation) for obj in objs
        ]

    @get("/type/{eval_type:str}")
    async def get_evaluations_by_type(
        self, evaluations_service: EvaluationsService, eval_type: str
    ) -> list[Evaluation]:
        """Get evaluations by type."""
        objs = await evaluations_service.list(type=eval_type)
        return [
            evaluations_service.to_schema(obj, schema_type=Evaluation) for obj in objs
        ]

    @get("/{evaluation_id:uuid}")
    async def get_evaluation(
        self,
        evaluations_service: EvaluationsService,
        evaluation_id: UUID = Parameter(
            title="Evaluation ID",
            description="The evaluation to retrieve.",
        ),
    ) -> Evaluation:
        """Get an evaluation by its ID."""
        obj = await evaluations_service.get(evaluation_id)
        return evaluations_service.to_schema(obj, schema_type=Evaluation)

    @patch("/{evaluation_id:uuid}")
    async def update_evaluation(
        self,
        evaluations_service: EvaluationsService,
        data: EvaluationUpdate,
        evaluation_id: UUID = Parameter(
            title="Evaluation ID",
            description="The evaluation to update.",
        ),
    ) -> Evaluation:
        """Update an evaluation."""
        obj = await evaluations_service.update(
            data, item_id=evaluation_id, auto_commit=True
        )
        return evaluations_service.to_schema(obj, schema_type=Evaluation)

    @delete("/{evaluation_id:uuid}")
    async def delete_evaluation(
        self,
        evaluations_service: EvaluationsService,
        evaluation_id: UUID = Parameter(
            title="Evaluation ID",
            description="The evaluation to delete.",
        ),
    ) -> None:
        """Delete an evaluation."""
        await evaluations_service.delete(evaluation_id)
