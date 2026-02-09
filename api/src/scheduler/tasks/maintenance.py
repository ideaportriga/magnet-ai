import traceback
from datetime import UTC, datetime, timedelta
from logging import getLogger

from scheduler.utils import get_interval_days
from services.agents.conversations.services import get_conversation_by_id
from services.agents.models import AgentConversationDataWithMessages
from services.agents.services import get_agent_by_system_name
from services.observability import observability_context
from services.observability.utils import observability_overrides

logger = getLogger(__name__)


async def execute_post_process_configuration_impl(**kwargs):
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


async def execute_cleanup_logs_impl(**kwargs):
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
