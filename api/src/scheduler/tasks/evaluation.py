import traceback
from logging import getLogger

from services.observability import observability_context

logger = getLogger(__name__)


async def execute_evaluation_impl(**kwargs):
    job_id = kwargs.get("job_id")

    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type="evaluation",
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        job_record = {
            "_id": job_id,
            "type": params.get("type"),
            "iteration_count": params.get("iteration_count", 1),
            "config": params.get("config", []),
            "result_entity": params.get("result_entity"),
        }

        from services.jobs.jobs_types.evaluate import evaluate

        result = await evaluate(job_record)

        logger.info(f"Successfully completed evaluation for job {job_id}")
        return result

    except Exception as e:
        logger.error(f"Error in execute_evaluation for job {job_id}: {str(e)}")
        traceback.print_exc()

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "params": params,
            },
        )
        raise
