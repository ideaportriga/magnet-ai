from typing import Annotated, Any

from litestar import Request, get, post
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from litestar.status_codes import HTTP_200_OK

from services.agents.conversations.services import (
    get_conversation,
    get_conversation_by_id,
)
from services.agents.models import (
    Agent,
    AgentConversationDataWithMessages,
    AgentConversationMessageAssistant,
    AgentConversationWithMessages,
    AgentExecute,
    AgentTest,
)
from services.agents.post_process.utils import post_process_conversation
from services.agents.services import execute_agent, get_agent_by_system_name
from services.observability import observability_context, observe
from services.observability.services import get_analytics_by_id
from services.observability.utils import observability_overrides

from .create_entity_controller import create_entity_controller

AgentsControllerBase = create_entity_controller(
    collection_name="agents",
    model=Agent,
)


class AgentTestResponse(AgentConversationMessageAssistant):
    trace_id: str | None = None


class AgentExecuteResponse(AgentConversationMessageAssistant):
    pass


class AgentsController(AgentsControllerBase):
    path = "/agents"
    tags = ["agents"]

    @observe(
        name="Conversation with agent",
        description="User either started a new conversation or continued an existing one with an agent.",
        channel="preview",
        source="preview",
    )
    @post("/test", status_code=HTTP_200_OK)
    async def agent_test(
        self, data: Annotated[AgentTest, Body()], trace_id: str | None = None
    ) -> AgentTestResponse:
        observability_context.update_current_trace(name=data.name, type="agent")

        observability_context.update_current_span(
            input={"User message": data.messages[-1].content}
        )

        try:
            result = await execute_agent(
                messages=data.messages,
                config_override=data.agent_config,
                variables=data.variables,
            )
        except Exception:
            # Handle exception as appropriate, e.g., log or re-raise
            raise

        observability_context.update_current_span(
            output={"Agent response": result.content},
        )

        return AgentTestResponse(
            **result.model_dump(),
            trace_id=trace_id or observability_context.get_current_trace_id(),
        )

    # This is duplicated in user routes. TODO - delete after verifying it's not used in admin panel
    @observe(
        name="Conversation with agent",
        description="User either started a new conversation or continued an existing one with an agent.",
        channel="production",
    )
    @post("/execute", status_code=HTTP_200_OK)
    async def agent_execute(
        self, data: Annotated[AgentExecute, Body()], request: Request
    ) -> AgentExecuteResponse:
        agent_config = await get_agent_by_system_name(data.agent_system_name)

        user_id = request.scope.get("user_id")
        observability_context.update_current_baggage(user_id=user_id)
        observability_context.update_current_trace(
            name=agent_config.name, type="agent", user_id=user_id
        )
        observability_context.update_current_span(
            input={"User message": data.messages[-1].content}
        )

        result = await execute_agent(
            config_override=agent_config.active_variant_value,
            messages=data.messages,
            variables=data.variables,
        )

        observability_context.update_current_span(
            output={"Agent response": result.content}
        )

        return AgentExecuteResponse(**result.model_dump())

    @get(
        "/{id:str}",
        summary="RetrieveConversation",
        description="Retrieves the details of a specific conversation by id.",
    )
    async def get_conversation_route(
        self,
        id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation to retrieve."
            ),
        ],
    ) -> dict[str, Any]:
        conversation = (
            await get_conversation(id, AgentConversationWithMessages)
        ).model_dump()
        if not conversation:
            raise NotFoundException()

        # Add information from analytics
        analytics_id = conversation.get("analytics_id")
        if analytics_id:
            analytics = await get_analytics_by_id(analytics_id)
            conversation["analytics"] = analytics

        return conversation

    # TODO: add observe decorator here
    @post(
        "/post_process_conversation",
        status_code=HTTP_200_OK,
        summary="Post-process conversation",
        description="Runs post-processing for a conversation by conversation_id.",
    )
    async def post_process_conversation_route(
        self,
        conversation_id: Annotated[str, Body()],
        prompt_template_system_name: str | None,
    ) -> dict[str, Any]:
        conversation_document = await get_conversation_by_id(conversation_id)
        conversation = AgentConversationDataWithMessages(**conversation_document)

        return await post_process_conversation(
            conversation_or_id=conversation_id,
            prompt_template_system_name=prompt_template_system_name,
            **observability_overrides(trace_id=conversation.trace_id),
        )
