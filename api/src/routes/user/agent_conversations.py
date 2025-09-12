from logging import getLogger
from typing import Annotated, Any

from litestar import Controller, Request, get, post
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession

from api.tags import TagNames
from services.agents.conversations import (
    add_user_message,
    copy_message,
    create_conversation,
    get_conversation,
    get_last_conversation_by_client_id,
    set_message_feedback,
)
from services.agents.conversations.services import get_conversation_by_id
from services.agents.models import (
    AgentConversationAddUserMessageRequest,
    AgentConversationAddUserMessageResponse,
    AgentConversationCreateRequest,
    AgentConversationMessageFeedbackRequest,
    AgentConversationWithMessagesPublic,
)
from services.agents.services import get_agent_by_system_name
from services.observability import (
    observability_context,
    observability_overrides,
    observe,
)

AgentConversationCreateResponse = AgentConversationWithMessagesPublic

logger = getLogger(__name__)


class AgentConversationsController(Controller):
    path = "/agent_conversations"
    tags = [TagNames.UserAgentConversations]

    @observe(
        name="New conversation started by user",
        description="User initiated a new conversation with an agent by writing a first message.",
        channel="production",
    )
    @post(
        summary="Create a new conversation",
        description="Creates a new conversation with an agent using the provided agent system name and user message content.",
    )
    async def create_conversation_route(
        self,
        data: AgentConversationCreateRequest,
        user_id: Annotated[
            str | None,
            Parameter(
                description="The unique identifier of the user creating the conversation.",
            ),
        ],
        request: Request,
        db_session: AsyncSession,
    ) -> AgentConversationCreateResponse:
        agent_config = await get_agent_by_system_name(data.agent)

        observability_context.update_current_baggage(
            source=request.headers.get("x-source") or "Runtime AI App",
            consumer_type=request.headers.get("x-consumer-type") or "agent",
            consumer_name=(
                request.headers.get("x-consumer-name") or agent_config.system_name
            ),
            user_id=user_id,
        )

        observability_context.update_current_trace(
            name=agent_config.name, type="agent", user_id=user_id
        )

        return await create_conversation(
            agent_config,
            data.user_message_content,
            data.client_id,
            data.variables,
            db_session,
        )

    @get(
        "/{conversation_id:str}",
        summary="Retrieve a conversation",
        description="Retrieves the details of a specific conversation by its unique identifier.",
    )
    async def get_conversation_route(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation to retrieve.",
            ),
        ],
    ) -> AgentConversationWithMessagesPublic:
        conversation = await get_conversation(conversation_id)
        return conversation

    @post(
        "/{conversation_id:str}/messages",
        summary="Add a message to a conversation",
        description="Adds a new user message to an existing conversation identified by its unique ID.",
    )
    async def add_message_route(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation to which the message will be added.",
            ),
        ],
        data: AgentConversationAddUserMessageRequest,
        user_id: Annotated[
            str | None,
            Parameter(
                description="The unique identifier of the user adding the message.",
            ),
        ],
    ) -> AgentConversationAddUserMessageResponse:
        conversation = await get_conversation_by_id(conversation_id)
        if not conversation:
            raise NotFoundException()

        trace_id: str | None = conversation.get("trace_id")
        if not trace_id:
            logger.warning(
                f"Cannot restore trace for conversation {conversation_id}, new trace will be created"
            )

        return await self._add_message_route(
            conversation, data, user_id, **observability_overrides(trace_id=trace_id)
        )

    @observe(
        name="New user message",
        description="User posted a new message to an existing conversation.",
        channel="production",
        source="Runtime AI App",
    )
    async def _add_message_route(
        self,
        conversation: dict[str, Any],
        data: AgentConversationAddUserMessageRequest,
        user_id: str | None,
    ):
        agent_config = await get_agent_by_system_name(str(conversation.get("agent")))

        observability_context.update_current_baggage(user_id=user_id)

        observability_context.update_current_trace(
            name=agent_config.name, type="agent", user_id=user_id
        )

        return await add_user_message(
            agent_config,
            conversation,
            data.user_message_content,
            data.action_call_confirmations,
        )

    @post(
        "/{conversation_id:str}/messages/{message_id:str}/feedback",
        status_code=HTTP_200_OK,
        summary="Provide feedback for a message",
        description="Allows the user to provide feedback for a specific message in a conversation.",
    )
    async def message_feedback(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation containing the message.",
            ),
        ],
        message_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the message for which feedback is being provided.",
            ),
        ],
        data: AgentConversationMessageFeedbackRequest,
    ) -> None:
        await set_message_feedback(
            conversation_id=conversation_id,
            message_id=message_id,
            data=data,
        )

    @post(
        "/{conversation_id:str}/messages/{message_id:str}/copy",
        status_code=HTTP_200_OK,
        summary="Indicate message copy",
        description="Indicates that a specific message in a conversation was copied by the user.",
    )
    async def copy_message(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation containing the message that was copied.",
            ),
        ],
        message_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the message that was copied.",
            ),
        ],
    ) -> None:
        await copy_message(conversation_id=conversation_id, message_id=message_id)

    @get(
        "/client/{client_id:str}",
        summary="Retrieve the last active conversation by client_id",
        description="Retrieves the most recent active conversation by client-side identifier, which is set when creating a new agent conversation.",
    )
    async def get_last_conversation_route(
        self,
        client_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the client whose conversation is being retrieved.",
            ),
        ],
    ) -> AgentConversationWithMessagesPublic:
        conversation = await get_last_conversation_by_client_id(client_id)
        if not conversation:
            raise NotFoundException()

        return conversation
