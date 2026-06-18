import asyncio
import uuid
from datetime import timedelta
from logging import getLogger
from typing import Any, Type, Union
from uuid import UUID

from sqlalchemy import desc, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypeVar

from core.config.app import alchemy
from core.db.models.agent_conversation import AgentConversation
from core.domain.agent_conversation.service import AgentConversationService
from services.agents.models import (
    Agent,
    AgentActionCallConfirmation,
    AgentConversationAddUserMessageResponse,
    AgentConversationDataWithMessages,
    AgentConversationMessage,
    AgentConversationMessageAssistantPublic,
    AgentConversationMessageFeedbackRequest,
    AgentConversationMessagePublic,
    AgentConversationMessageRole,
    AgentConversationMessageUser,
    AgentConversationMessageUserPublic,
    AgentConversationWithMessages,
    AgentConversationWithMessagesPublic,
    AgentConversationMessageProcessingStatus,
    WebhookCallbackConfig,
)
from services.agents.post_process.utils import extract_analytics_from_conversation
from services.agents.services import execute_agent, get_agent_by_system_name
from services.webhooks import deliver_agent_reply
from services.common.models import ConversationMessageFeedback
from services.observability import (
    observability_context,
    observability_overrides,
    observe,
)
from services.observability.models import FeatureType, ObservedFeature
from services.telemetry.services import (
    record_tool_response_copy,
    record_tool_response_feedback,
)
from stores import RecordNotFoundError
from utils.datetime_utils import utc_now

logger = getLogger(__name__)


async def create_conversation(
    agent_system_name_or_config: str | Agent,
    content: str,
    client_id: str | None = None,
    variables: dict[str, str] | None = None,
    db_session: AsyncSession | None = None,
    is_async: bool = False,
    callback: WebhookCallbackConfig | None = None,
) -> AgentConversationWithMessagesPublic:
    # Get agent config
    if isinstance(agent_system_name_or_config, str):
        agent_config = await get_agent_by_system_name(agent_system_name_or_config)
    else:
        agent_config = agent_system_name_or_config

    # Record agent execution (used for metrics and analytics)
    observed_feature = ObservedFeature(
        type=FeatureType.AGENT,
        id=str(agent_config.id) if agent_config.id else None,
        system_name=agent_config.system_name,
        display_name=agent_config.name,
        variant=agent_config.active_variant,
    )
    with observability_context.observe_feature(observed_feature) as instance_id:
        observability_context.update_current_span(
            name="Create conversation", extra_data={"status": "In Progress"}
        )

        timestamp_now = utc_now()

        messages: list[AgentConversationMessage] = [
            AgentConversationMessageUser(
                id=uuid.uuid4(),
                content=content,
                created_at=timestamp_now,
            ),
        ]
        if not is_async:
            assistant_message = await execute_agent(
                system_name_or_config=agent_system_name_or_config,
                messages=messages,
                variables=variables,
            )
            messages.append(assistant_message)
            message_processing_status = (
                AgentConversationMessageProcessingStatus.COMPLETED
            )
        else:
            message_processing_status = (
                AgentConversationMessageProcessingStatus.PROCESSING
            )
        conversation_data = AgentConversationDataWithMessages(
            client_id=client_id,
            agent=agent_config.system_name,
            created_at=timestamp_now,
            last_user_message_at=timestamp_now,
            messages=messages,
            trace_id=observability_context.get_current_trace_id(),
            analytics_id=instance_id,
            variables=variables,
            message_processing_status=message_processing_status,
            callback=callback,
        )

        # Replace MongoDB insert with SQLAlchemy service
        async with db_session or alchemy.get_session() as session:
            service = AgentConversationService(session=session)
            conversation_record = await service.create(
                conversation_data.model_dump(), auto_commit=True
            )

            conversation_id = str(conversation_record.id)

        observability_context.update_current_trace(
            extra_data={"conversation_id": conversation_id}
        )

        messages_public: list[AgentConversationMessagePublic] = [
            AgentConversationMessageUserPublic(
                id=message.id,
                content=message.content,
                created_at=message.created_at,
                action_call_confirmations=message.action_call_confirmations,
            )
            if isinstance(message, AgentConversationMessageUser)
            else AgentConversationMessageAssistantPublic(
                id=message.id,
                content=message.content,
                created_at=message.created_at,
                action_call_requests=message.action_call_requests,
            )
            for message in messages
        ]

        conversation_public = AgentConversationWithMessagesPublic(
            id=UUID(conversation_id),
            messages=messages_public,
            agent=conversation_data.agent,
            created_at=conversation_data.created_at,
            last_user_message_at=conversation_data.last_user_message_at,
            trace_id=conversation_data.trace_id,
            analytics_id=conversation_data.analytics_id,
            message_processing_status=conversation_data.message_processing_status,
        )

        extracted_analytics = await extract_analytics_from_conversation(conversation_id)

        observability_context.update_current_baggage(
            conversation_id=conversation_id, conversation_data=extracted_analytics
        )
    if not is_async:
        observability_context.update_current_span(
            input={"User message": content},
            output={"Agent response": assistant_message.content},
        )

    return conversation_public


async def get_conversation_by_id(conversation_id: str) -> dict[str, Any]:
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        record = await service.get_one_or_none(id=conversation_id)
        if not record:
            raise RecordNotFoundError()
        return service.to_schema(
            record, schema_type=AgentConversationDataWithMessages
        ).model_dump()


ConversationType = TypeVar(
    "ConversationType",
    bound=Union["AgentConversationWithMessages", "AgentConversationWithMessagesPublic"],
)


async def get_conversation(
    conversation_id: str,
    conversation_class: Type[ConversationType] = AgentConversationWithMessagesPublic,
) -> ConversationType:
    document = await get_conversation_by_id(conversation_id)

    conversation = conversation_class(
        **document,
    )

    return conversation


async def get_last_conversation_by_client_id(client_id: str):
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        records = await service.list(
            AgentConversation.client_id == client_id,
            or_(
                AgentConversation.status.is_(None),
                func.lower(AgentConversation.status) != "closed",
            ),
            order_by=[desc(AgentConversation.created_at)],
        )
        record = records[0] if records else None

        if not record:
            return None

        last_conversation = service.to_schema(
            record, schema_type=AgentConversationWithMessagesPublic
        )

        updated_at = last_conversation.last_user_message_at
        if updated_at:
            updated_at_datetime = updated_at
            if updated_at_datetime >= utc_now() - timedelta(hours=24):
                return last_conversation

        return None


async def add_user_message(
    agent_system_name_or_config: str | Agent,
    conversation_or_id: dict[str, Any] | str,
    user_message_content: str | None,
    action_call_confirmations: list[AgentActionCallConfirmation] | None = None,
):
    # Get agent config
    if isinstance(agent_system_name_or_config, str):
        agent_config = await get_agent_by_system_name(agent_system_name_or_config)
    else:
        agent_config = agent_system_name_or_config

    # Get existing conversation
    if isinstance(conversation_or_id, str):
        conversation_id = conversation_or_id
        conversation_record = await get_conversation_by_id(conversation_or_id)
    else:
        conversation_id = str(conversation_or_id.get("id"))
        conversation_record = conversation_or_id
    conversation = AgentConversationDataWithMessages(**conversation_record)

    # Get analytics ID
    analytics_id: str | None = conversation_record.get("analytics_id")
    if not analytics_id:
        logger.warning(
            f"Cannot restore analytics for conversation {conversation_id}, new analytics record will be created"
        )

    # Record agent execution (used for metrics and analytics)
    observed_feature = ObservedFeature(
        type=FeatureType.AGENT,
        id=str(agent_config.id) if agent_config.id else None,
        system_name=agent_config.system_name,
        display_name=agent_config.name,
    )
    with observability_context.observe_feature(observed_feature, analytics_id):
        observability_context.update_current_span(name="Add user message")

        user_message: AgentConversationMessageUser = AgentConversationMessageUser(
            id=uuid.uuid4(),
            content=user_message_content,
            action_call_confirmations=action_call_confirmations,
            created_at=utc_now(),
        )

        assistant_message = await execute_agent(
            system_name_or_config=conversation.agent,
            messages=conversation.messages + [user_message],
            variables=conversation.variables,
        )

        async with alchemy.get_session() as session:
            service = AgentConversationService(session=session)

            # Update conversation with new messages
            conversation.last_user_message_at = utc_now()
            conversation.messages.append(user_message)
            conversation.messages.append(assistant_message)
            conversation.message_processing_status = (
                AgentConversationMessageProcessingStatus.COMPLETED
            )
            # Update the conversation in the database
            await service.update(
                item_id=conversation_id,
                data=conversation.model_dump(),
                auto_commit=True,
            )

        response = AgentConversationAddUserMessageResponse(
            user_message=AgentConversationMessageUserPublic(
                id=user_message.id,
                content=user_message.content,
                created_at=user_message.created_at,
                action_call_confirmations=user_message.action_call_confirmations,
            ),
            assistant_message=AgentConversationMessageAssistantPublic(
                id=assistant_message.id,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                action_call_requests=assistant_message.action_call_requests,
            ),
            trace_id=observability_context.get_current_trace_id(),
            analytics_id=analytics_id,
        )

        conversation_analytics = await extract_analytics_from_conversation(
            conversation_id
        )

        observability_context.update_current_baggage(
            conversation_data=conversation_analytics
        )

    observability_context.update_current_span(
        input={"User message": user_message_content},
        output={"Agent response": assistant_message.content},
    )

    return response


async def set_message_feedback(
    conversation_id: str,
    message_id: str,
    data: AgentConversationMessageFeedbackRequest,
    *,
    consumer_name: str | None = None,
) -> None:
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        updated = await service.update_message_feedback(
            db_session=session,
            conversation_id=conversation_id,
            message_id=message_id,
            feedback_data=data.model_dump(),
        )
        if not updated:
            raise RecordNotFoundError()

    conversation_document = await get_conversation_by_id(conversation_id)
    conversation = AgentConversationDataWithMessages(**conversation_document)
    payload = data.model_dump()

    await _record_feedback_observability(
        conversation=conversation,
        conversation_id=conversation_id,
        message_id=message_id,
        payload=payload,
        consumer_name=consumer_name,
    )


async def _record_feedback_observability(
    *,
    conversation: AgentConversationDataWithMessages,
    conversation_id: str,
    message_id: str,
    payload: dict[str, Any],
    consumer_name: str | None,
) -> None:
    feedback_type = payload.get("type") or "unknown"
    trace_overrides = observability_overrides(
        trace_id=conversation.trace_id,
        consumer_name=consumer_name,
    )

    @observability_context.observe(
        name=f"Set message feedback ({feedback_type})",
        description="Record user feedback for an agent message",
        channel="production",
        source="Runtime AI App",
    )
    async def _run():
        observability_context.update_current_span(
            extra_data={
                "message_id": message_id,
                "feedback": payload,
                "feedback_type": feedback_type,
                "feedback_reason": payload.get("reason"),
                "feedback_comment": payload.get("comment"),
            },
        )

        agent = await get_agent_by_system_name(conversation.agent)
        feature = ObservedFeature(
            type=FeatureType.AGENT,
            id=str(agent.id) if agent.id else None,
            system_name=agent.system_name,
            display_name=agent.name,
        )

        with observability_context.observe_feature(feature, conversation.analytics_id):
            observability_context.update_current_span(
                name="Setting user feedback",
                extra_data={
                    "message_id": message_id,
                    "feedback_type": feedback_type,
                    "feedback_reason": payload.get("reason"),
                    "feedback_comment": payload.get("comment"),
                },
            )
            observability_context.update_current_trace(
                extra_data={"conversation_id": conversation_id}
            )
            await record_tool_response_feedback(
                trace_id=conversation.trace_id,
                analytics_id=conversation.analytics_id,
                feedback=AgentConversationMessageFeedbackRequest(**payload),
            )

            analytics = await extract_analytics_from_conversation(conversation_id)
            observability_context.update_current_baggage(
                conversation_id=conversation_id,
                conversation_data=analytics,
            )

    await _run(**trace_overrides)


async def set_message_custom_feedback(
    conversation_id: str, message_id: str, data: ConversationMessageFeedback
):
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)

        success = await service.update_message_custom_feedback(
            db_session=session,
            conversation_id=conversation_id,
            message_id=message_id,
            custom_feedback_data=data.model_dump(),
        )

        if not success:
            raise RecordNotFoundError()


async def copy_message(conversation_id: str, message_id: str):
    conversation_document = await get_conversation_by_id(conversation_id)
    conversation = AgentConversationDataWithMessages(**conversation_document)

    if message_id:
        async with alchemy.get_session() as session:
            service = AgentConversationService(session=session)

            success = await service.update_message_copied_status(
                db_session=session,
                conversation_id=conversation_id,
                message_id=message_id,
                copied=True,
            )

            if not success:
                raise RecordNotFoundError()

    await record_tool_response_copy(
        trace_id=conversation.trace_id,
        analytics_id=conversation.analytics_id,
    )


async def update_conversation_status(
    conversation_id: str,
    status: str,
) -> bool:
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)

        updated = await service.update_conversation_status(
            db_session=session,
            conversation_id=conversation_id,
            status=status,
        )

        if not updated:
            raise RecordNotFoundError()

    return updated


@observe(
    name="New conversation started by user",
    description="User initiated a new conversation with an agent by writing a first message.",
    channel="production",
)
async def add_assistant_message(
    conversation_or_id: dict[str, Any] | str,
):
    if isinstance(conversation_or_id, str):
        conversation_id = conversation_or_id
        conversation_record = await get_conversation_by_id(conversation_or_id)
    else:
        conversation_id = str(conversation_or_id.get("id"))
        conversation_record = conversation_or_id

    conversation = AgentConversationDataWithMessages(**conversation_record)
    agent_config = await get_agent_by_system_name(conversation.agent)
    observability_context.update_current_trace(name=agent_config.name, type="agent")
    assistant_message = await execute_agent(
        system_name_or_config=conversation.agent,
        messages=conversation.messages,
        variables=conversation.variables,
    )
    conversation.messages.append(assistant_message)
    conversation.message_processing_status = (
        AgentConversationMessageProcessingStatus.COMPLETED
    )
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        await service.update(
            item_id=conversation_id,
            data=conversation.model_dump(),
            auto_commit=True,
        )
    return assistant_message


async def get_missing_messages(
    conversation_id: str, message_count: int
) -> dict[str, Any]:
    """Get messages that are missing based on the provided message count."""
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        record = await service.get_one_or_none(id=conversation_id)
        if not record:
            raise RecordNotFoundError()

        # Get all messages from JSONB
        all_messages = (
            record.messages
            if record.messages and isinstance(record.messages, list)
            else []
        )
        total_count = len(all_messages)

        # Get only missing messages (after the provided count)
        missing_messages = (
            all_messages[message_count:] if message_count < total_count else []
        )

        # Convert to public format
        messages_public: list[AgentConversationMessagePublic] = []
        for message in missing_messages:
            # Handle UUID conversion - it might be a string or UUID object
            message_id = message.get("id")
            if isinstance(message_id, str):
                message_id = UUID(message_id)
            elif not isinstance(message_id, UUID):
                continue  # Skip invalid messages

            role = message.get("role")
            if role == "user" or role == AgentConversationMessageRole.USER:
                messages_public.append(
                    AgentConversationMessageUserPublic(
                        id=message_id,
                        content=message.get("content"),
                        created_at=message.get("created_at"),
                        action_call_confirmations=message.get(
                            "action_call_confirmations"
                        ),
                    )
                )
            else:  # assistant
                messages_public.append(
                    AgentConversationMessageAssistantPublic(
                        id=message_id,
                        content=message.get("content"),
                        created_at=message.get("created_at"),
                        action_call_requests=message.get("action_call_requests"),
                    )
                )
        return {
            "messages": [msg.model_dump() for msg in messages_public],
            "message_processing_status": record.message_processing_status,
            "total_count": total_count,
            "returned_count": len(messages_public),
        }


async def get_message_processing_status(
    conversation_id: str,
) -> AgentConversationMessageProcessingStatus:
    conversation_record = await get_conversation_by_id(conversation_id)
    conversation = AgentConversationDataWithMessages(**conversation_record)
    return conversation.message_processing_status


async def update_message_processing_status(
    conversation_id: str,
    message_processing_status: AgentConversationMessageProcessingStatus,
):
    conversation_record = await get_conversation_by_id(conversation_id)
    conversation = AgentConversationDataWithMessages(**conversation_record)
    conversation.message_processing_status = message_processing_status
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        updated = await service.update(
            item_id=conversation_id,
            data=conversation.model_dump(),
            auto_commit=True,
        )
    if not updated:
        raise RecordNotFoundError()
    return message_processing_status


# ---------------------------------------------------------------------------
# Rapid-fire handling (2.1): cancel in-flight, answer only the latest message.
#
# Each new user message bumps ``processing_generation`` on the conversation and
# is persisted immediately, so earlier (un-answered) user messages remain in the
# stored history and are automatically folded into the next turn's context. A
# background turn captures the generation it runs under and only persists its
# reply if that is still current (multi-worker-safe guard). On THIS worker we
# also cancel the previous task outright so its LLM call is interrupted.
# ---------------------------------------------------------------------------

# In-process registry of running turns (per worker). Cross-worker supersession
# is enforced by the DB generation guard at persist time.
_running_turns: dict[str, asyncio.Task] = {}


def _register_turn(conversation_id: str, task: asyncio.Task) -> None:
    _running_turns[conversation_id] = task

    def _cleanup(finished: asyncio.Task, cid: str = conversation_id) -> None:
        if _running_turns.get(cid) is finished:
            _running_turns.pop(cid, None)

    task.add_done_callback(_cleanup)


def cancel_local_turn(conversation_id: str) -> None:
    """Cancel any in-flight turn for this conversation on the current worker."""
    task = _running_turns.get(conversation_id)
    if task and not task.done():
        logger.info(
            "Cancelling superseded in-flight turn for conversation %s", conversation_id
        )
        task.cancel()


@observe(
    name="Agent reply (async)",
    description="Background processing of a user message. Only the latest message's turn is persisted; superseded turns are discarded.",
    channel="production",
)
async def run_agent_turn(conversation_id: str, generation: int) -> None:
    """Execute one agent turn and persist its reply only if still current."""
    try:
        conversation_record = await get_conversation_by_id(conversation_id)
        conversation = AgentConversationDataWithMessages(**conversation_record)
        agent_config = await get_agent_by_system_name(conversation.agent)
        observability_context.update_current_trace(name=agent_config.name, type="agent")
        assistant_message = await execute_agent(
            system_name_or_config=conversation.agent,
            messages=conversation.messages,
            variables=conversation.variables,
        )
    except asyncio.CancelledError:
        logger.info(
            "Turn cancelled (conversation %s, generation %s)",
            conversation_id,
            generation,
        )
        raise
    except Exception:
        logger.exception(
            "Turn failed (conversation %s, generation %s)",
            conversation_id,
            generation,
        )
        async with alchemy.get_session() as session:
            service = AgentConversationService(session=session)
            await service.persist_turn_result_if_current(
                session,
                conversation_id,
                generation,
                status=AgentConversationMessageProcessingStatus.FAILED.value,
            )
        return

    assistant_dict = assistant_message.model_dump(mode="json")
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        applied = await service.persist_turn_result_if_current(
            session,
            conversation_id,
            generation,
            append_message=assistant_dict,
            status=AgentConversationMessageProcessingStatus.COMPLETED.value,
        )

    # Deliver the reply via outbound webhook only for the winning (current) turn.
    if applied and conversation.callback:
        await deliver_agent_reply(
            url=conversation.callback.url,
            payload={
                "conversation_id": conversation_id,
                "message": {
                    "id": str(assistant_message.id),
                    "role": "assistant",
                    "content": assistant_message.content,
                    "created_at": assistant_message.created_at.isoformat(),
                },
            },
            headers=conversation.callback.headers,
        )


def schedule_turn(conversation_id: str, generation: int, **observability_kwargs):
    """Cancel any local in-flight turn and schedule a fresh one."""
    cancel_local_turn(conversation_id)
    task = asyncio.create_task(
        run_agent_turn(conversation_id, generation, **observability_kwargs)
    )
    _register_turn(conversation_id, task)
    return task


def schedule_initial_turn(
    conversation_id: str, generation: int = 0, **observability_kwargs
):
    """Schedule the first turn of a freshly created async conversation."""
    return schedule_turn(conversation_id, generation, **observability_kwargs)


async def register_and_schedule_user_message(
    conversation_record: dict[str, Any],
    user_message_content: str | None,
    action_call_confirmations: list[AgentActionCallConfirmation] | None = None,
    *,
    callback: WebhookCallbackConfig | None = None,
    **observability_kwargs,
) -> AgentConversationMessageProcessingStatus:
    """Persist a new user message, supersede prior processing, and schedule a turn."""
    conversation_id = str(conversation_record.get("id"))

    user_message = AgentConversationMessageUser(
        id=uuid.uuid4(),
        content=user_message_content,
        action_call_confirmations=action_call_confirmations,
        created_at=utc_now(),
    )

    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        generation = await service.bump_processing_generation(
            session,
            conversation_id,
            append_message=user_message.model_dump(mode="json"),
            status=AgentConversationMessageProcessingStatus.PROCESSING.value,
            callback=callback.model_dump(mode="json") if callback else None,
        )

    if generation is None:
        raise RecordNotFoundError()

    schedule_turn(conversation_id, generation, **observability_kwargs)
    return AgentConversationMessageProcessingStatus.PROCESSING


async def edit_message_content(
    conversation_id: str,
    message_id: str,
    content: str,
    edited_by: str | None = None,
) -> None:
    """Override an assistant message's content (operator/external edit, 2.3)."""
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        updated = await service.update_message_content(
            db_session=session,
            conversation_id=conversation_id,
            message_id=message_id,
            content=content,
            edited_by=edited_by,
        )
    if not updated:
        raise RecordNotFoundError()


async def start_webhook_conversation(
    agent_system_name_or_config: str | Agent,
    user_message_content: str,
    callback: WebhookCallbackConfig,
    conversation_id: str | None = None,
    client_id: str | None = None,
    variables: dict[str, str] | None = None,
) -> tuple[str, AgentConversationMessageProcessingStatus]:
    """Webhook-driven (async) invocation entry point (2.2).

    Continues an existing conversation (by id, else by client_id) or creates a
    new one, schedules processing, and returns immediately. The reply is pushed
    to ``callback`` once ready.
    """
    if isinstance(agent_system_name_or_config, str):
        agent_config = await get_agent_by_system_name(agent_system_name_or_config)
    else:
        agent_config = agent_system_name_or_config

    existing_record: dict[str, Any] | None = None
    if conversation_id:
        try:
            existing_record = await get_conversation_by_id(str(conversation_id))
        except RecordNotFoundError:
            existing_record = None
    elif client_id:
        last = await get_last_conversation_by_client_id(client_id)
        if last:
            existing_record = await get_conversation_by_id(str(last.id))

    if existing_record:
        cid = str(existing_record["id"])
        trace_id = existing_record.get("trace_id")
        status = await register_and_schedule_user_message(
            existing_record,
            user_message_content,
            None,
            callback=callback,
            **observability_overrides(trace_id=trace_id),
        )
        return cid, status

    conversation = await create_conversation(
        agent_config,
        user_message_content,
        client_id,
        variables,
        is_async=True,
        callback=callback,
    )
    cid = str(conversation.id)
    schedule_initial_turn(
        cid, **observability_overrides(trace_id=conversation.trace_id)
    )
    return cid, conversation.message_processing_status
