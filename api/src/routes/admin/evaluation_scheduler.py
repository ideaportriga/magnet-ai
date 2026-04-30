"""Evaluation scheduler route (TaskIQ-backed)."""

import logging
from typing import Any, Dict, List

from litestar import Controller, post
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.admin_ops import create_or_update_job
from tasks.types import (
    JobDefinition,
    JobType,
    RunConfiguration,
    RunConfigurationType,
)

logger = logging.getLogger(__name__)


class EvaluationConfig(BaseModel):
    """Configuration for a single evaluation target."""

    system_name: str
    test_set_system_names: List[str]
    variants: List[str]


class EvaluationJobRequest(BaseModel):
    """Request payload for creating an evaluation job."""

    name: str
    evaluation_type: str  # "rag_eval" or "prompt_eval"
    iteration_count: int = 1
    config: List[EvaluationConfig]
    result_entity: str = "evaluations"


class EvaluationSchedulerController(Controller):
    path = "/evaluation-scheduler"

    @post("/create-evaluation-job")
    async def create_evaluation_job(
        self, data: EvaluationJobRequest, db_session: AsyncSession
    ) -> Dict[str, Any]:
        try:
            evaluation_params = {
                "type": data.evaluation_type,
                "iteration_count": data.iteration_count,
                "config": [cfg.model_dump() for cfg in data.config],
                "result_entity": data.result_entity,
            }
            job_definition = JobDefinition(
                name=data.name,
                job_type=JobType.ONE_TIME_IMMEDIATE,
                run_configuration=RunConfiguration(
                    type=RunConfigurationType.EVALUATION, params=evaluation_params
                ),
                job_id=None,
                interval=None,
                notification_email=None,
                cron=None,
                scheduled_start_time=None,
                status=None,
                timezone=None,
            )
            result = await create_or_update_job(job_definition, db_session)
            logger.info(f"Created evaluation job: {result}")
            return {
                "success": True,
                "message": "Evaluation job created successfully",
                "job_details": result,
            }
        except Exception as e:
            logger.error(f"Error creating evaluation job: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create evaluation job",
            }
