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
    AgentConversationMessageUser,
    AgentConversationMessageUserPublic,
    AgentConversationWithMessages,
    AgentConversationWithMessagesPublic,
)
from services.agents.post_process.utils import extract_analytics_from_conversation
from services.agents.services import execute_agent, get_agent_by_system_name
from services.common.models import ConversationMessageFeedback
from services.observability import observability_context, observability_overrides
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

        assistant_message = await execute_agent(
            system_name_or_config=agent_system_name_or_config,
            messages=messages,
            variables=variables,
        )

        messages.append(assistant_message)

        conversation_data = AgentConversationDataWithMessages(
            client_id=client_id,
            agent=agent_config.system_name,
            created_at=timestamp_now,
            last_user_message_at=timestamp_now,
            messages=messages,
            trace_id=observability_context.get_current_trace_id(),
            analytics_id=instance_id,
            variables=variables,
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
        )

        extracted_analytics = await extract_analytics_from_conversation(conversation_id)

        observability_context.update_current_baggage(
            conversation_id=conversation_id, conversation_data=extracted_analytics
        )

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
                func.lower(AgentConversation.status) != "closed"
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
