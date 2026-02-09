import traceback
from logging import getLogger

from services.observability import observability_context

logger = getLogger(__name__)


async def execute_custom_function_impl(**kwargs):
    job_id = kwargs.get("job_id")
    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )
        return True
    except Exception as e:
        logger.error(f"Error in execute_custom_function for job {job_id}: {str(e)}")
        traceback.print_exc()

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise
