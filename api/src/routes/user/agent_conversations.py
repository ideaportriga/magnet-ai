import asyncio
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
    get_missing_messages,
    get_last_conversation_by_client_id,
    set_message_feedback,
    add_assistant_message,
    update_message_processing_status,
    update_conversation_status,
)
from services.agents.conversations.services import get_conversation_by_id
from services.agents.models import (
    AgentConversationAddUserMessageRequest,
    AgentConversationAddUserMessageResponse,
    AgentConversationCreateRequest,
    AgentConversationMessageFeedbackRequest,
    AgentConversationWithMessagesPublic,
    AgentConversationMessageProcessingStatus,
)
from services.agents.services import get_agent_by_system_name
from services.observability import (
    observability_context,
    observability_overrides,
    observe,
)
from stores import RecordNotFoundError

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

    @post(
        "/{conversation_id:str}/close",
        status_code=HTTP_200_OK,
        summary="Close a conversation by ID",
        description=(
            "Closes an agent conversation by its ID. Once closed, it will no longer be retrieved "
            "when querying by client_id, allowing a new conversation to be started with the same client_id."
        ),
    )
    async def close_conversation_route(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation to close.",
            ),
        ],
    ) -> None:
        conversation = await get_conversation(conversation_id)
        if not conversation:
            raise NotFoundException()

        await update_conversation_status(conversation_id, "Closed")

    @post(
        "/client/{client_id:str}/close",
        status_code=HTTP_200_OK,
        summary="Close the last active conversation by client_id",
        description=(
            "Closes the most recent active conversation for the given client_id. "
            "Once closed, the next request with this client_id will create a new conversation."
        ),
    )
    async def close_conversation_by_client_id_route(
        self,
        client_id: Annotated[
            str,
            Parameter(
                description="The client identifier whose active conversation should be closed.",
            ),
        ],
    ) -> None:
        conversation = await get_last_conversation_by_client_id(client_id)
        if not conversation:
            raise NotFoundException()

        conversation_id = str(conversation.id)
        await update_conversation_status(conversation_id, "Closed")

    ## Asynchronously
    @post(
        "/async",
        summary="Create a new conversation asynchronously",
    )
    async def create_conversation_asynchronously(
        self,
        data: AgentConversationCreateRequest,
        db_session: AsyncSession,
    ) -> AgentConversationWithMessagesPublic:
        conversation = await create_conversation(
            data.agent,
            data.user_message_content,
            data.client_id,
            data.variables,
            db_session,
            is_async=True,
        )  ### is_async=True means that agent message wont be processed immediately
        asyncio.create_task(add_assistant_message(str(conversation.id)))
        return conversation

    @post(
        "/{conversation_id:str}/messages/async",
        status_code=HTTP_200_OK,
        summary="Add a message to a conversation asynchronically",
    )
    async def add_message_route_asynchronically(
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
    ) -> AgentConversationMessageProcessingStatus:
        try:
            conversation = await get_conversation_by_id(conversation_id)
        except RecordNotFoundError:
            raise NotFoundException()

        trace_id: str | None = conversation.get("trace_id")
        if not trace_id:
            logger.warning(
                f"Cannot restore trace for conversation {conversation_id}, new trace will be created"
            )
        message_processing_status = await update_message_processing_status(
            str(conversation["id"]), AgentConversationMessageProcessingStatus.PROCESSING
        )

        asyncio.create_task(
            self._add_message_route(
                conversation,
                data,
                user_id,
                **observability_overrides(trace_id=trace_id),
            )
        )
        return message_processing_status

    @get(
        "/{conversation_id:str}/missing_messages",
        summary="Get missing messages",
        description="Retrieves only the messages that are missing based on the provided message count. Returns messages after the specified count.",
    )
    async def get_missing_messages_route(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation.",
            ),
        ],
        message_count: Annotated[
            int,
            Parameter(
                description="The number of messages the client already has. Returns messages after this count.",
                ge=0,
            ),
        ],
    ) -> dict[str, Any]:
        try:
            missing_messages = await get_missing_messages(
                conversation_id, message_count
            )
            return missing_messages
        except RecordNotFoundError:
            raise NotFoundException()
