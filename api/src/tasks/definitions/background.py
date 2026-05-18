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


@broker.task(task_name="process_teams_recording_notification", timeout=3600)
@observe(name="Process Teams recording notification (bg)", channel="Background")
async def process_teams_recording_notification_bg_task(
    event_id: str, trace_id: str | None = None
) -> None:
    """Process one Graph recording-ready notification durably.

    The webhook handler stages the original notification payload in
    ``teams_webhook_event`` and enqueues this task with the row id.
    Re-deliveries of the same event_id replay work against the same row;
    duplicates from Graph are filtered earlier at intake time.

    The task survives API rolling deploys because the payload lives in
    Postgres and the queue lives in the broker.

    ``trace_id`` is bound to the contextvar so any log emitted inside the
    pipeline carries the same correlation id — see § P1-3.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select, update

    from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent
    from core.db.session import async_session_maker
    from services.agents.teams.note_taker import (
        handle_recordings_ready_notifications,
    )
    from services.agents.teams.note_taker_worker_registry import (
        get_worker_registry,
    )
    from services.agents.teams.trace_context import bind_trace_id

    with bind_trace_id(trace_id):
        async with async_session_maker() as session:
            result = await session.execute(
                select(TeamsWebhookEvent).where(TeamsWebhookEvent.id == UUID(event_id))
            )
            event = result.scalar_one_or_none()
            if event is None:
                logger.warning(
                    "process_teams_recording_notification: event %s not found",
                    event_id,
                )
                return
            if event.status in {"done"}:
                logger.info(
                    "process_teams_recording_notification: event %s already done, skipping",
                    event_id,
                )
                return
            notification = dict(event.notification or {})
            webhook_kind = event.webhook_kind

            await session.execute(
                update(TeamsWebhookEvent)
                .where(TeamsWebhookEvent.id == event.id)
                .values(status="processing")
            )
            await session.commit()

        if webhook_kind != "recordings-ready":
            logger.info(
                "process_teams_recording_notification: ignoring kind=%s for event %s",
                webhook_kind,
                event_id,
            )
            async with async_session_maker() as session:
                await session.execute(
                    update(TeamsWebhookEvent)
                    .where(TeamsWebhookEvent.id == UUID(event_id))
                    .values(
                        status="done",
                        processed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
            return

        payload_for_runtime = {"value": [notification]}

        # Classify the worst failure seen across runtimes; on transient
        # failures we re-enqueue with a short backoff (see § P0-4).
        from services.agents.teams.webhook_errors import (
            UnauthorizedWebhookError,
            classify_exception,
        )

        error_message: str | None = None
        worst_classification: str = "ok"
        try:
            registry = await get_worker_registry()
            runtimes = [rt for _, rt in registry.all_runtimes()]
            if not runtimes:
                logger.warning(
                    "process_teams_recording_notification: no runtimes available for event %s",
                    event_id,
                )
            # Pull the prior attempt count once so we can decide retry.
            from sqlalchemy import select

            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(TeamsWebhookEvent.retry_count).where(
                            TeamsWebhookEvent.id == UUID(event_id)
                        )
                    )
                ).scalar_one_or_none()
            previous_retry_count = int(row or 0)

            for runtime in runtimes:
                try:
                    await handle_recordings_ready_notifications(
                        runtime,
                        payload_for_runtime,
                        notify_user=(previous_retry_count == 0),
                    )
                except UnauthorizedWebhookError as exc:
                    logger.warning(
                        "process_teams_recording_notification: unauthorized for event %s: %s",
                        event_id,
                        exc,
                    )
                    if error_message is None:
                        error_message = f"unauthorized: {exc}"[:2000]
                    worst_classification = "unauthorized"
                except Exception as exc:  # noqa: BLE001 — keep going across runtimes
                    logger.exception(
                        "process_teams_recording_notification: runtime failed for event %s: %s",
                        event_id,
                        exc,
                    )
                    if error_message is None:
                        error_message = f"{type(exc).__name__}: {exc}"[:2000]
                    bucket = classify_exception(exc)
                    if worst_classification != "unauthorized":
                        worst_classification = bucket

            # Retry policy: transient failures get re-enqueued with
            # exponential backoff, capped at MAX_RETRIES. See § P0-4.
            MAX_RETRIES = 3
            should_retry = (
                worst_classification == "transient"
                and previous_retry_count < MAX_RETRIES
            )

            if should_retry:
                new_count = previous_retry_count + 1
                async with async_session_maker() as session:
                    await session.execute(
                        update(TeamsWebhookEvent)
                        .where(TeamsWebhookEvent.id == UUID(event_id))
                        .values(
                            status="received",
                            retry_count=new_count,
                            error=error_message,
                        )
                    )
                    await session.commit()

                delay_seconds = min(30 * (2**previous_retry_count), 300)
                logger.info(
                    "process_teams_recording_notification: retrying event %s in %ss (attempt %d/%d)",
                    event_id,
                    delay_seconds,
                    new_count,
                    MAX_RETRIES,
                )
                # Durable retry: write a one-shot into `taskiq_schedules`
                # via `schedule_by_time`. The scheduler process picks it
                # up at `retry_at` regardless of whether the current
                # worker survives the backoff window — the in-memory
                # `asyncio.create_task(sleep+kiq)` pattern this replaces
                # lost retries when the worker was killed mid-sleep,
                # defeating the durability we set out to gain in § P0-2.
                from datetime import timedelta

                from tasks import schedule_source

                retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                await process_teams_recording_notification_bg_task.schedule_by_time(
                    schedule_source,
                    retry_at,
                    event_id=event_id,
                    trace_id=trace_id,
                )
                return  # don't mark failed yet
        except Exception as exc:  # outer guard so finally still records status
            logger.exception(
                "process_teams_recording_notification: unexpected worker failure: %s",
                exc,
            )
            if error_message is None:
                error_message = f"{type(exc).__name__}: {exc}"[:2000]

        async with async_session_maker() as session:
            await session.execute(
                update(TeamsWebhookEvent)
                .where(TeamsWebhookEvent.id == UUID(event_id))
                .values(
                    status="failed" if error_message else "done",
                    error=error_message,
                    processed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()


@broker.task(task_name="process_teams_lifecycle_event", timeout=600)
@observe(name="Process Teams lifecycle event (bg)", channel="Background")
async def process_teams_lifecycle_event_bg_task(
    event_id: str, trace_id: str | None = None
) -> None:
    """Process one Graph recordings-lifecycle notification.

    See ``services/agents/teams/lifecycle_worker.py`` for the full
    description. Kept short here so the broker doesn't block on an
    inactive subscription forever.
    """
    from services.agents.teams.lifecycle_worker import process_lifecycle_event
    from services.agents.teams.trace_context import bind_trace_id

    with bind_trace_id(trace_id):
        await process_lifecycle_event(UUID(event_id))


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


@broker.task(task_name="note_taker_kg_ingest_background", timeout=3600)
@observe(name="Note-taker KG ingest (bg)", channel="Background")
async def note_taker_kg_ingest_bg_task(
    graph_system_name: str,
    sections: dict[str, str],
    meeting_part: str,
    item_id: str,
    date_part: str,
    job_id: str | None = None,
    trace_id: str | None = None,
) -> None:
    """Background KG ingestion for note-taker post-processing outputs.

    Replaces the previous `asyncio.create_task(run_background_ingest(...))`
    fire-and-forget call (see NOTE_TAKER_REVISION_PLAN.md §3.1 P0-d).

    The `integration_attempt(...)` journal lives **inside** the task body,
    not at the call site — the call site only enqueues, so its outcome is
    "kiq succeeded" which is uninteresting. Wrapping the real work here
    means `note_taker_integration_attempt` status reflects whether the
    embedding actually ran, and failed attempts are eligible for the
    outbox retry sweep.
    """
    from types import SimpleNamespace
    from uuid import uuid4

    from sqlalchemy import select

    from core.db.models.knowledge_graph import KnowledgeGraph
    from core.db.session import async_session_maker
    from services.agents.teams.integration_journal import integration_attempt
    from services.agents.teams.note_taker_utils import _build_note_taker_filename
    from services.knowledge_graph.sources.api_ingest.api_ingest_source import (
        ApiIngestDataSource,
        run_background_ingest,
    )

    if not graph_system_name or not sections:
        return

    async def _do_ingest() -> int:
        async with async_session_maker() as session:
            stmt = select(KnowledgeGraph).where(
                KnowledgeGraph.system_name == graph_system_name
            )
            graph = (await session.execute(stmt)).scalars().first()
            if graph is None:
                logger.warning(
                    "Knowledge graph %s not found for note-taker embedding.",
                    graph_system_name,
                )
                return 0

            data_source = ApiIngestDataSource(source_name="Note Taker")
            source = await data_source.get_or_create_source(session, graph.id)
            graph_id = graph.id
            source_id = UUID(str(source.id))

        items: list[SimpleNamespace] = []
        for kind, content in sections.items():
            if not content:
                continue
            items.append(
                SimpleNamespace(
                    kind="text",
                    filename=_build_note_taker_filename(
                        kind=kind,
                        meeting_id=meeting_part,
                        item_id=item_id,
                        date_part=date_part,
                        ext=".txt",
                    ),
                    text=content,
                    file_bytes=None,
                    source_metadata=None,
                    stored_file_id=None,
                )
            )

        if not items:
            return 0

        await run_background_ingest(
            ingestion_id=str(uuid4()),
            graph_id=graph_id,
            source_id=source_id,
            items=items,
        )
        return len(items)

    # Skip the journal wrapper when there's no job_id (admin-preview /
    # ad-hoc calls bypass job tracking). The work still runs.
    if not job_id:
        await _do_ingest()
        return

    retry_payload = {
        "graph_system_name": graph_system_name,
        "sections": sections,
        "meeting_part": meeting_part,
        "item_id": item_id,
        "date_part": date_part,
        "job_id": job_id,
        "trace_id": trace_id,
    }
    async with integration_attempt(
        job_id=job_id,
        integration_kind="knowledge_graph",
        trace_id=trace_id,
        retry_payload=retry_payload,
    ) as proceed:
        if proceed:
            await _do_ingest()
