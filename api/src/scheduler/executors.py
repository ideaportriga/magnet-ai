"""Job executor functions for the SAQ-based scheduler.

Each task function follows SAQ's signature: ``async def task(ctx, **kwargs)``.
The first positional argument ``ctx`` is the SAQ context dict.

Recurring jobs re-enqueue themselves after completion using
``_reschedule_if_recurring``.
"""

import traceback
from datetime import UTC, datetime, timedelta
from functools import wraps
from logging import getLogger

from scheduler.types import JobDefinition, JobStatus, JobType, RunConfigurationType
from scheduler.utils import update_job_status
from services.agents.conversations.services import get_conversation_by_id
from services.agents.models import AgentConversationDataWithMessages
from services.agents.services import get_agent_by_system_name
from services.observability import observability_context, observe
from services.observability.models import FeatureType
from services.observability.utils import observability_overrides

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_interval_days(interval):
    print(f"Interval: {interval}")
    if interval == "1D":
        return 1
    if interval == "3D":
        return 3
    if interval == "7D":
        return 7
    raise ValueError("Invalid interval value")


async def _reschedule_if_recurring(ctx, *, job_id: str, job_definition: dict):
    """If the job is recurring, enqueue the next execution in SAQ."""
    jd = JobDefinition.model_validate(job_definition)
    if jd.job_type != JobType.RECURRING or not jd.cron:
        return

    try:
        from croniter import croniter

        cron_params = {k: v for k, v in jd.cron.model_dump().items() if v is not None}
        minute = str(cron_params.get("minute", "*"))
        hour = str(cron_params.get("hour", "*"))
        day = str(cron_params.get("day", "*"))
        month = str(cron_params.get("month", "*"))
        day_of_week = str(cron_params.get("day_of_week", "*"))

        cron_expr = f"{minute} {hour} {day} {month} {day_of_week}"
        now = datetime.now(UTC)
        cron_iter = croniter(cron_expr, now)
        next_dt = cron_iter.get_next(datetime)
        next_epoch = next_dt.timestamp()

        # Get the queue from SAQ context
        queue = ctx.get("queue")
        if queue is None:
            logger.error(
                f"No queue in SAQ context; cannot reschedule recurring job {job_id}"
            )
            return

        # Determine the task name from the run_configuration type
        handler = RUN_CONFIG_HANDLERS.get(jd.run_configuration.type)
        if handler is None:
            logger.error(
                f"No handler for {jd.run_configuration.type}; cannot reschedule"
            )
            return

        await queue.enqueue(
            handler.__qualname__,
            key=f"job:{job_id}",
            scheduled=next_epoch,
            job_id=job_id,
            job_definition=job_definition,
            params=jd.run_configuration.params,
        )

        next_run_iso = next_dt.isoformat()
        await update_job_status(job_id, JobStatus.WAITING, {"next_run": next_run_iso})
        logger.info(f"Rescheduled recurring job {job_id} for {next_run_iso}")

    except Exception as e:
        logger.error(f"Failed to reschedule recurring job {job_id}: {e}")


# ---------------------------------------------------------------------------
# Decorator – wraps each task to track PROCESSING / ERROR status
# ---------------------------------------------------------------------------


def with_progress_status(func):
    """Set status to PROCESSING before execution; ERROR on exception."""

    @wraps(func)
    async def wrapper(ctx, **kwargs):
        job_id = kwargs.get("job_id")
        try:
            if job_id:
                await update_job_status(job_id, JobStatus.PROCESSING)
            result = await func(ctx, **kwargs)
            # On success, update status and reschedule if recurring
            if job_id:
                job_definition = kwargs.get("job_definition")
                current_time = datetime.now(UTC).isoformat()
                if job_definition:
                    jd = JobDefinition.model_validate(job_definition)
                    if jd.job_type == JobType.RECURRING:
                        # Status will be set to WAITING by _reschedule_if_recurring
                        await update_job_status(
                            job_id, JobStatus.WAITING, {"last_run": current_time}
                        )
                        await _reschedule_if_recurring(
                            ctx, job_id=job_id, job_definition=job_definition
                        )
                    else:
                        await update_job_status(
                            job_id, JobStatus.COMPLETED, {"last_run": current_time}
                        )
                else:
                    await update_job_status(
                        job_id, JobStatus.COMPLETED, {"last_run": current_time}
                    )
            return result
        except Exception as e:
            if job_id:
                try:
                    current_time = datetime.now(UTC).isoformat()
                    job_definition = kwargs.get("job_definition")
                    # Even on error, reschedule recurring jobs
                    if job_definition:
                        jd = JobDefinition.model_validate(job_definition)
                        if jd.job_type == JobType.RECURRING:
                            await update_job_status(
                                job_id,
                                JobStatus.WAITING,
                                {"last_run": current_time, "error": str(e)},
                            )
                            await _reschedule_if_recurring(
                                ctx, job_id=job_id, job_definition=job_definition
                            )
                        else:
                            await update_job_status(
                                job_id,
                                JobStatus.ERROR,
                                {"last_run": current_time, "error": str(e)},
                            )
                    else:
                        await update_job_status(job_id, JobStatus.ERROR)
                except Exception as update_error:
                    logger.error(
                        f"Failed to update job status for job {job_id}: {str(update_error)}"
                    )
            raise

    return wrapper


# ---------------------------------------------------------------------------
# Task functions
# ---------------------------------------------------------------------------


@with_progress_status
@observe(name="Custom job", channel="Job")
async def execute_custom_function(ctx, **kwargs):
    """Execute a custom function with the given parameters."""
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


@with_progress_status
@observe(name="Sync knowledge source", channel="Job")
async def execute_sync_collection(ctx, **kwargs):
    """Execute a sync collection job with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
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

        system_name = params.get("system_name")

        if not system_name:
            logger.error(f"Missing system_name parameter for job {job_id}")
            return False

        collection_id = system_name

        from services.utils.get_ids_by_system_names import get_ids_by_system_names

        collection_id = await get_ids_by_system_names(system_name, "collections")
        if not collection_id:
            logger.error(
                f"Collection not found for system_name '{system_name}' in job {job_id}"
            )
            return False

        if isinstance(collection_id, list):
            if collection_id:
                collection_id = collection_id[0]
            else:
                logger.error(
                    f"Empty collection_id list for system_name '{system_name}' in job {job_id}"
                )
                return False

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
        raise


@with_progress_status
async def execute_post_process_configuration(ctx, **kwargs):
    """Execute a post-process configuration job with the given parameters."""
    job_id = kwargs.get("job_id")

    try:
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

                async with alchemy.get_session() as session:
                    service = AgentConversationService(session=session)

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
        raise


@with_progress_status
@observe(name="Evaluation job", channel="Job")
async def execute_evaluation(ctx, **kwargs):
    """Execute an evaluation job with the given parameters."""
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

        from services.jobs.jobs_types.evaluate import evaluate

        job_record = {
            "_id": job_id,
            "type": params.get("type"),
            "iteration_count": params.get("iteration_count", 1),
            "config": params.get("config", []),
            "result_entity": params.get("result_entity"),
        }

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


@with_progress_status
@observe(name="Sync knowledge graph source", channel="Job")
async def execute_sync_knowledge_graph_source(ctx, **kwargs):
    """Execute a knowledge graph source sync job."""
    job_id = kwargs.get("job_id")

    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type="sync_knowledge_graph_source",
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        graph_id = params.get("graph_id")
        source_id = params.get("source_id")

        if not graph_id or not source_id:
            logger.error(f"Missing graph_id or source_id for job {job_id}")
            return False

        from uuid import UUID

        from core.config.app import alchemy
        from core.domain.knowledge_graph.service import KnowledgeGraphSourceService

        async with alchemy.get_session() as session:
            service = KnowledgeGraphSourceService(session=session)
            await service.sync_source(
                session, UUID(str(graph_id)), UUID(str(source_id))
            )

        logger.info(
            f"Successfully started sync for graph {graph_id} source {source_id} in job {job_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error in execute_sync_knowledge_graph_source for job {job_id}: {str(e)}"
        )
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


@with_progress_status
@observe(name="Cleanup logs", channel="Job")
async def execute_cleanup_logs(ctx, **kwargs):
    """Execute a cleanup job to delete old traces and metrics.

    Params:
        retention_days: Number of days to retain logs. Logs older than this will be deleted.
        cleanup_traces: Whether to cleanup traces table (default: True)
        cleanup_metrics: Whether to cleanup metrics table (default: True)
    """
    job_id = kwargs.get("job_id")

    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type="cleanup_logs",
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        retention_days = params.get("retention_days", 30)
        cleanup_traces = params.get("cleanup_traces", True)
        cleanup_metrics = params.get("cleanup_metrics", True)

        if retention_days < 1:
            logger.error(f"Invalid retention_days value: {retention_days}")
            return False

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        deleted_traces = 0
        deleted_metrics = 0

        from sqlalchemy import delete

        from core.config.app import alchemy
        from core.db.models.metric.metric import Metric
        from core.db.models.trace.trace import Trace

        async with alchemy.get_session() as session:
            if cleanup_traces:
                result = await session.execute(
                    delete(Trace).where(Trace.created_at < cutoff_date)
                )
                deleted_traces = result.rowcount
                logger.info(
                    f"Deleted {deleted_traces} traces older than {retention_days} days"
                )

            if cleanup_metrics:
                result = await session.execute(
                    delete(Metric).where(Metric.created_at < cutoff_date)
                )
                deleted_metrics = result.rowcount
                logger.info(
                    f"Deleted {deleted_metrics} metrics older than {retention_days} days"
                )

            await session.commit()

        observability_context.update_current_trace(
            extra_data={
                "deleted_traces": deleted_traces,
                "deleted_metrics": deleted_metrics,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

        logger.info(
            f"Successfully completed cleanup logs job {job_id}: "
            f"deleted {deleted_traces} traces and {deleted_metrics} metrics"
        )
        return True

    except Exception as e:
        logger.error(f"Error in execute_cleanup_logs for job {job_id}: {str(e)}")
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


# Mapping of run configuration types to execution functions directly
RUN_CONFIG_HANDLERS = {
    RunConfigurationType.CUSTOM: execute_custom_function,
    RunConfigurationType.SYNC_COLLECTION: execute_sync_collection,
    RunConfigurationType.POST_PROCESS_CONVERSATION: execute_post_process_configuration,
    RunConfigurationType.EVALUATION: execute_evaluation,
    RunConfigurationType.SYNC_KNOWLEDGE_GRAPH_SOURCE: execute_sync_knowledge_graph_source,
    RunConfigurationType.CLEANUP_LOGS: execute_cleanup_logs,
}
