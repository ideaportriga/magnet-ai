"""Evaluation + post-process-conversation tasks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any

from services.observability import observability_context, observe
from tasks.broker import broker
from tasks.status import with_job_status

logger = getLogger(__name__)


def _interval_days(interval: str) -> int:
    mapping = {"1D": 1, "3D": 3, "7D": 7}
    if interval not in mapping:
        raise ValueError(f"Invalid interval value: {interval}")
    return mapping[interval]


@broker.task(task_name="evaluate", timeout=1800)
@with_job_status
@observe(name="Evaluation job", channel="Job")
async def evaluate_task(
    *,
    job_id: str | None = None,
    type: str | None = None,
    config: list[dict] | None = None,
    iteration_count: int = 1,
    result_entity: str | None = None,
    **_: Any,
) -> dict:
    from services.jobs.jobs_types.evaluate import evaluate

    if not type:
        raise ValueError(f"Missing 'type' for evaluation job {job_id}")
    if not config:
        raise ValueError(f"Missing/empty 'config' for evaluation job {job_id}")

    required = ["system_name", "test_set_system_names", "variants"]
    for i, item in enumerate(config):
        missing = [f for f in required if f not in item]
        if missing:
            raise ValueError(
                f"Config item [{i}] in evaluation job {job_id} missing: {missing}"
            )

    # Mirror the extra_data shape written by the legacy APScheduler executor
    # so the evaluation-job traces keep their filterability (UI reads
    # extra_data.params.system_name via JSONB path).
    observability_context.update_current_trace(
        type="evaluation",
        extra_data={
            "job_id": job_id,
            "params": {
                "type": type,
                "config": config,
                "iteration_count": iteration_count,
                "result_entity": result_entity,
            },
        },
    )

    job_record = {
        "_id": job_id,
        "type": type,
        "iteration_count": iteration_count,
        "config": config,
        "result_entity": result_entity,
    }
    result = await evaluate(job_record)
    logger.info("evaluate job %s completed", job_id)
    return result


@broker.task(task_name="post_process_conversation", timeout=1800)
@with_job_status
@observe(name="Post-process conversations", channel="Job")
async def post_process_conversation_task(
    *,
    job_id: str | None = None,
    agent_system_names: list[str] | None = None,
    **_: Any,
) -> bool:
    from core.config.app import alchemy
    from core.db.models.agent_conversation import AgentConversation
    from core.domain.agent_conversation.service import AgentConversationService
    from services.agents.conversations.services import get_conversation_by_id
    from services.agents.models import AgentConversationDataWithMessages
    from services.agents.post_process.utils import post_process_conversation
    from services.agents.services import get_agent_by_system_name
    from services.observability.utils import observability_overrides

    if not agent_system_names:
        raise ValueError(f"Missing agent_system_names for job {job_id}")

    for agent_system_name in agent_system_names:
        try:
            agent = await get_agent_by_system_name(agent_system_name)
            if not agent or not agent.active_variant_value.settings:
                continue

            close_interval = (
                agent.active_variant_value.settings.conversation_closure_interval
            )
            if not close_interval:
                continue

            days = _interval_days(close_interval)
            boundary = datetime.now(UTC) - timedelta(days=days)

            async with alchemy.get_session() as session:
                service = AgentConversationService(session=session)
                conversations = await service.list(
                    AgentConversation.status != "closed",
                    AgentConversation.agent == agent_system_name,
                    AgentConversation.created_at <= boundary,
                )

            if not conversations:
                continue

            pp = agent.active_variant_value.post_processing
            if not pp or not pp.enabled:
                continue

            for conv in conversations:
                conversation_id = str(conv.id)
                try:
                    conv_doc = await get_conversation_by_id(conversation_id)
                    conversation = AgentConversationDataWithMessages(**conv_doc)
                    await post_process_conversation(
                        conversation_or_id=conversation_id,
                        prompt_template_system_name=pp.template,
                        **observability_overrides(trace_id=conversation.trace_id),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "post_process_conversation failed for %s: %s",
                        conversation_id,
                        exc,
                    )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "post_process_conversation agent %s failed: %s", agent_system_name, exc
            )

    logger.info("post_process_conversation job %s completed", job_id)
    return True
