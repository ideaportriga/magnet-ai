"""Fire-and-forget background tasks.

Replacements for `spawn_background_task()` callsites. Survive API rollouts,
observable via the `taskiq_messages` table, retried only for the idempotent
tasks listed in `middlewares.retry.IDEMPOTENT_TASK_NAMES`.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any
from uuid import UUID

from services.observability import observe
from tasks.broker import broker

logger = getLogger(__name__)


@broker.task(task_name="sync_kg_source_background", timeout=3600)
@observe(name="Sync KG source (bg)", channel="Background")
async def sync_kg_source_bg_task(graph_id: str, source_id: str) -> None:
    """Background KG source sync invoked from HTTP handlers."""
    from core.config.app import alchemy
    from services.knowledge_graph.sources.sync_services import sync_source

    async with alchemy.get_session() as session:
        await sync_source(session, UUID(graph_id), UUID(source_id))


@broker.task(task_name="entity_extraction_background", timeout=3600)
@observe(name="Entity extraction (bg)", channel="Background")
async def entity_extraction_bg_task(graph_id: str, payload: dict[str, Any]) -> None:
    """Background entity extraction pipeline run."""
    from services.knowledge_graph.llm_entity_extraction import (
        run_entity_extraction_background,
    )

    await run_entity_extraction_background(UUID(graph_id), payload)


@broker.task(task_name="deep_research_background", timeout=7200)
@observe(name="Deep research (bg)", channel="Background")
async def deep_research_bg_task(run_id: str) -> None:
    """Background deep research run."""
    from services.deep_research.services import run_deep_research_workflow

    await run_deep_research_workflow(run_id)


@broker.task(task_name="note_taker_preview_background", timeout=3600)
@observe(name="Note-taker preview (bg)", channel="Background")
async def note_taker_preview_bg_task(
    job_id: str,
    settings_id: str,
    source_url: str | None = None,
    participants: list[str] | None = None,
    stt_model_system_name: str | None = None,
    object_key: str | None = None,
    upload_filename: str | None = None,
    upload_content_type: str | None = None,
) -> None:
    """Background note-taker preview job.

    Accepts either a remote `source_url` (downloaded by the runner) or a
    pre-uploaded `object_key` (the upload path stages the file in object
    storage before enqueueing, so a worker on a separate process can pick
    up the job without losing the bytes).
    """
    from services.agents.teams.note_taker_settings import _run_preview_job_background

    await _run_preview_job_background(
        job_id=job_id,
        settings_id=settings_id,
        source_url=source_url,
        object_key=object_key,
        upload_filename=upload_filename,
        upload_content_type=upload_content_type,
        participants=participants or [],
        stt_model_system_name=stt_model_system_name,
    )


@broker.task(task_name="note_taker_rerun_background", timeout=3600)
@observe(name="Note-taker rerun (bg)", channel="Background")
async def note_taker_rerun_bg_task(
    job_id: str,
    settings_id: str,
    speaker_mapping: dict[str, Any] | None = None,
    extra_keyterms: list[str] | None = None,
    meeting_notes: str | None = None,
) -> None:
    """Background note-taker postprocessing rerun."""
    from services.agents.teams.note_taker_settings import (
        _rerun_postprocessing_background,
    )

    await _rerun_postprocessing_background(
        job_id=job_id,
        settings_id=settings_id,
        speaker_mapping=speaker_mapping or {},
        extra_keyterms=extra_keyterms or [],
        meeting_notes=meeting_notes,
    )


@broker.task(task_name="add_assistant_message_background", timeout=1800)
@observe(name="Assistant message (bg)", channel="Background")
async def add_assistant_message_bg_task(conversation_id: str) -> None:
    """Background agent assistant message generation."""
    from services.agents.conversations.services import add_assistant_message

    await add_assistant_message(conversation_id)


@broker.task(task_name="add_user_message_background", timeout=1800)
@observe(name="User message (bg)", channel="Background")
async def add_user_message_bg_task(
    conversation_id: str,
    user_message_content: str,
    action_call_confirmations: list[dict[str, Any]] | None = None,
    user_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    """Background agent user-message ingestion + assistant response generation."""
    from core.domain.agent_conversation.schemas import (
        AgentConversationAddUserMessageRequest,
    )
    from services.agents.conversations.services import (
        add_user_message,
        get_conversation_by_id,
    )
    from services.agents.services import get_agent_by_system_name
    from services.observability import observability_context
    from services.observability.utils import observability_overrides

    conversation = await get_conversation_by_id(conversation_id)
    agent_config = await get_agent_by_system_name(str(conversation.get("agent")))
    observability_context.update_current_baggage(user_id=user_id)
    observability_context.update_current_trace(
        name=agent_config.name, type="agent", user_id=user_id
    )
    overrides = observability_overrides(trace_id=trace_id)  # noqa: F841
    data = AgentConversationAddUserMessageRequest(
        user_message_content=user_message_content,
        action_call_confirmations=action_call_confirmations or [],
    )
    await add_user_message(
        agent_config,
        conversation,
        data.user_message_content,
        data.action_call_confirmations,
    )


@broker.task(task_name="api_ingest_background", timeout=7200)
@observe(name="API ingest (bg)", channel="Background")
async def api_ingest_bg_task(
    ingestion_id: str,
    graph_id: str,
    source_id: str,
    items: list[dict[str, Any]],
) -> None:
    """Background API-ingest pipeline for a KG source."""
    from services.knowledge_graph.sources.api_ingest.api_ingest_source import (
        run_background_ingest,
    )

    await run_background_ingest(
        ingestion_id=ingestion_id,
        graph_id=UUID(graph_id),
        source_id=UUID(source_id),
        items=items,
    )
