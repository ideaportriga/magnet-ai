"""Job executor functions for the scheduler.
These functions handle the actual execution of scheduled jobs.
"""

import traceback
from datetime import UTC, datetime, timedelta
from functools import wraps
from logging import getLogger

from scheduler.types import JobStatus, RunConfigurationType
from scheduler.utils import update_job_status
from services.agents.conversations.services import get_conversation_by_id
from services.agents.models import AgentConversationDataWithMessages
from services.agents.services import get_agent_by_system_name
from services.observability import observability_context, observe
from services.observability.models import FeatureType
from services.observability.utils import observability_overrides

logger = getLogger(__name__)


def get_interval_days(interval):
    print(f"Interval: {interval}")
    if interval == "1D":
        return 1
    if interval == "3D":
        return 3
    if interval == "7D":
        return 7
    raise ValueError("Invalid interval value")


# Decorator to set status to PROGRESS before execution (async version)
def with_progress_status(func):
    @wraps(func)
    async def wrapper(**kwargs):
        job_id = kwargs.get("job_id")

        try:
            if job_id:
                await update_job_status(job_id, JobStatus.PROCESSING)
            return await func(**kwargs)
        except Exception as e:
            # If there's an error and job_id exists, update status to ERROR
            if job_id:
                try:
                    await update_job_status(job_id, JobStatus.ERROR)
                except Exception as update_error:
                    logger.error(
                        f"Failed to update job status for job {job_id}: {str(update_error)}"
                    )
            # Re-raise the original exception
            raise e

    return wrapper


@with_progress_status
@observe(name="Custom job", channel="Job")
async def execute_custom_function(**kwargs):
    """Execute a custom function with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
        # Extract job information and parameters
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

        # Error status will be set by with_progress_status decorator
        raise e


@with_progress_status
@observe(name="Sync knowledge source", channel="Job")
async def execute_sync_collection(**kwargs):
    """Execute a sync collection job with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
        # Extract job information and parameters
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type=FeatureType.KNOWLEDGE_SOURCE.value,
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        # Extract system_name from params
        system_name = params.get("system_name")

        if not system_name:
            logger.error(f"Missing system_name parameter for job {job_id}")
            return False

        # Get collection_id from system_name
        collection_id = system_name

        # This is a system name, not an ID
        from services.utils.get_ids_by_system_names import get_ids_by_system_names

        collection_id = await get_ids_by_system_names(system_name, "collections")
        if not collection_id:
            logger.error(
                f"Collection not found for system_name '{system_name}' in job {job_id}"
            )
            return False

        # Handle case where collection_id is a list
        if isinstance(collection_id, list):
            if collection_id:
                collection_id = collection_id[0]  # Take the first ID
            else:
                logger.error(
                    f"Empty collection_id list for system_name '{system_name}' in job {job_id}"
                )
                return False

        # Create event loop and run the async sync_collection method
        # Import here to avoid circular imports
        from routes.admin.knowledge_sources import sync_collection_standalone

        result = await sync_collection_standalone(collection_id)

        if not result:
            logger.warning(
                f"Sync collection returned False for collection_id '{collection_id}' in job {job_id}"
            )
            return False

        logger.info(f"Successfully completed sync collection for job {job_id}")
        return True

    except Exception as e:
        logger.error(f"Error in execute_sync_collection for job {job_id}: {str(e)}")
        traceback.print_exc()

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "params": params,
            },
        )

        # Error status will be set by with_progress_status decorator
        raise e


@with_progress_status
async def execute_post_process_configuration(**kwargs):
    """Execute a post-process configuration job with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
        # job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        agents_system_names = params.get("agent_system_names")

        if not agents_system_names:
            logger.error(f"Missing agent_system_names parameter for job {job_id}")
            return False

        from core.config.app import alchemy
        from core.db.models.agent_conversation import AgentConversation
        from core.domain.agent_conversation.service import AgentConversationService

        for agent_system_name in agents_system_names:
            try:
                agent = await get_agent_by_system_name(agent_system_name)
                if not agent:
                    logger.warning(f"Agent not found: {agent_system_name}")
                    continue

                if not agent.active_variant_value.settings:
                    logger.info(f"Agent {agent_system_name} has no settings, skipping")
                    continue

                agent_close_interval = (
                    agent.active_variant_value.settings.conversation_closure_interval
                )

                if not agent_close_interval:
                    logger.info(
                        f"Agent {agent_system_name} has no closure interval, skipping"
                    )
                    continue

                days = get_interval_days(agent_close_interval)
                now = datetime.now(UTC)
                time_boundary = now - timedelta(days=days)

                # Use SQLAlchemy to find conversations
                async with alchemy.get_session() as session:
                    service = AgentConversationService(session=session)

                    # Find conversations that match criteria
                    conversations = await service.list(
                        AgentConversation.status != "closed",
                        AgentConversation.agent == agent_system_name,
                        AgentConversation.created_at <= time_boundary,
                    )

                if not conversations:
                    logger.info(f"No conversations found for agent {agent_system_name}")
                    continue

                from services.agents.post_process.utils import post_process_conversation

                for conv in conversations:
                    conversation_id = str(conv.id)
                    conversation_document = await get_conversation_by_id(
                        conversation_id
                    )
                    conversation = AgentConversationDataWithMessages(
                        **conversation_document
                    )

                    post_processing = agent.active_variant_value.post_processing
                    if not post_processing or not post_processing.enabled:
                        logger.info(
                            f"Post-processing disabled for agent {agent_system_name}"
                        )
                        continue

                    try:
                        await post_process_conversation(
                            conversation_or_id=conversation_id,
                            prompt_template_system_name=post_processing.template,
                            **observability_overrides(trace_id=conversation.trace_id),
                        )
                        logger.info(
                            f"Successfully post-processed conversation {conversation_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to post-process conversation {conversation_id}: {str(e)}"
                        )
                        continue

            except Exception as e:
                logger.error(f"Error processing agent {agent_system_name}: {str(e)}")
                continue

        return True

    except Exception as e:
        logger.error(
            f"Error in execute_post_process_configuration for job {job_id}: {str(e)}"
        )
        traceback.print_exc()

        # Error status will be set by with_progress_status decorator
        raise e


@with_progress_status
@observe(name="Evaluation job", channel="Job")
async def execute_evaluation(**kwargs):
    """Execute an evaluation job with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
        # Extract job information and parameters
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

        # Import here to avoid circular imports
        from services.jobs.jobs_types.evaluate import evaluate

        # Transform scheduler params to run_job format
        job_record = {
            "_id": job_id,
            "type": params.get("type"),  # "rag_eval" or "prompt_eval"
            "iteration_count": params.get("iteration_count", 1),
            "config": params.get("config", []),
            "result_entity": params.get("result_entity"),
        }

        # Execute the evaluation
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

        # Error status will be set by with_progress_status decorator
        raise e


# Mapping of run configuration types to execution functions directly
RUN_CONFIG_HANDLERS = {
    RunConfigurationType.CUSTOM: execute_custom_function,
    RunConfigurationType.SYNC_COLLECTION: execute_sync_collection,
    RunConfigurationType.POST_PROCESS_CONVERSATION: execute_post_process_configuration,
    RunConfigurationType.EVALUATION: execute_evaluation,
}
