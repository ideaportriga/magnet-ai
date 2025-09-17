from services.agents.models import AgentActionCallResponse
from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams
from services.observability import observability_context, observe
from services.observability.models import SpanType


@observe(
    name="Call API",
    description="Call external API to retrieve data or perform actions in external systems, enabling agent to interact with third-party services and resources.",
    type=SpanType.TOOL,
)
async def action_execute_api_tool(
    tool_provider: str,
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    server = tool_provider
    tool = tool_system_name
    input_params = ApiToolCallInputParams(**arguments)

    observability_context.update_current_span(
        input={
            "API server system name": server,
            "API tool system name": tool,
            "Input params": input_params.model_dump(),
        },
    )

    api_tool_call = ApiToolCall(
        server=server,
        tool=tool,
        input_params=input_params,
        variables=variables,
    )

    api_tool_execute_result = await call_api_server_tool(api_tool_call)

    result = AgentActionCallResponse(
        content=api_tool_execute_result.content,  # TODO - could it be useful to also add status code here?
        verbose_details=api_tool_execute_result.model_dump(),
    )

    return result
