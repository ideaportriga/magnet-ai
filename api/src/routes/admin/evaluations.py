from litestar import get, patch
from litestar.exceptions import (
    NotFoundException,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.evaluation.services import (
    list_evaluations_with_aggregations,
    update_evaluation_score,
)

from .create_entity_controller import create_entity_controller

# Base entity controller
EvaluationsBaseController = create_entity_controller(
    path_param="/evaluations",
    collection_name="evaluations",
)


class ScoreUpdateRequest(BaseModel):
    id: str
    result_id: str
    score: float
    score_comment: str | None = None


class EvaluationsController(EvaluationsBaseController):
    path = "/evaluations"
    tags = ["evaluations"]

    @get("/list")
    async def list_evaluations(self, db_session: AsyncSession) -> list[dict]:
        """List evaluations with aggregated metrics using SQLAlchemy."""
        return await list_evaluations_with_aggregations(db_session)

    @patch("/set_score")
    async def set_score(
        self, data: ScoreUpdateRequest, db_session: AsyncSession
    ) -> dict:
        """Update evaluation result score using SQLAlchemy."""
        try:
            success = await update_evaluation_score(
                db_session=db_session,
                evaluation_id=data.id,
                result_id=data.result_id,
                score=data.score,
                score_comment=data.score_comment,
            )

            if not success:
                raise NotFoundException(detail="Document or result not found")

            return {"message": "Score updated successfully"}

        except Exception as e:
            raise NotFoundException(detail=f"Database error: {e!s}")
