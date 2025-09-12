from typing import Protocol

from services.agents.actions.action_execute_api import action_execute_api
from services.agents.actions.action_execute_mcp_tool import action_execute_mcp_tool
from services.agents.actions.action_execute_prompt_template import (
    action_execute_prompt_template,
)
from services.agents.actions.action_execute_rag import action_execute_rag
from services.agents.actions.action_execute_retrieval import action_execute_retrieval
from services.agents.models import (
    AgentActionCallRequest,
    AgentActionCallResponse,
    AgentActionType,
)


class ActionFunctionProtocol(Protocol):
    async def __call__(
        self,
        tool_system_name: str,
        arguments: dict,
        variables: dict[str, str] | None = None,
    ) -> AgentActionCallResponse: ...


class ActionProvidedFunctionProtocol(Protocol):
    async def __call__(
        self,
        tool_provider: str,
        tool_system_name: str,
        arguments: dict,
        variables: dict[str, str] | None = None,
    ) -> AgentActionCallResponse: ...


EXECUTE_AGENT_ACTION_FUNCTION_MAP: dict[AgentActionType, ActionFunctionProtocol] = {
    AgentActionType.RAG: action_execute_rag,
    AgentActionType.RETRIEVAL: action_execute_retrieval,
    AgentActionType.API: action_execute_api,
    AgentActionType.PROMPT_TEMPLATE: action_execute_prompt_template,
}


EXECUTE_AGENT_PROVIDED_ACTION_FUNCTION_MAP: dict[
    AgentActionType, ActionProvidedFunctionProtocol
] = {
    AgentActionType.MCP_TOOL: action_execute_mcp_tool,
}


async def execute_agent_action(
    action_call_request: AgentActionCallRequest,
) -> AgentActionCallResponse:
    action_type = action_call_request.action_type

    if execute_agent_action_function := EXECUTE_AGENT_ACTION_FUNCTION_MAP.get(
        action_type
    ):
        return await execute_agent_action_function(
            tool_system_name=action_call_request.action_tool_system_name,
            arguments=action_call_request.arguments,
            variables=action_call_request.variables,
        )

    if execute_agent_action_function := EXECUTE_AGENT_PROVIDED_ACTION_FUNCTION_MAP.get(
        action_type
    ):
        assert action_call_request.action_tool_provider, (
            f"Provider is not defined for action {action_call_request.action_system_name}"
        )

        return await execute_agent_action_function(
            tool_provider=action_call_request.action_tool_provider,
            tool_system_name=action_call_request.action_tool_system_name,
            arguments=action_call_request.arguments,
            variables=action_call_request.variables,
        )

    raise ValueError(
        f"Agent action type '{action_type}' is not supported ({action_call_request.action_system_name=})",
    )
