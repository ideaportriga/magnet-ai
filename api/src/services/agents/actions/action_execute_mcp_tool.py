import json

from mcp.types import TextContent

from services.agents.models import AgentActionCallResponse
from services.mcp_servers.services import call_mcp_server_tool
from services.observability import observability_context, observe
from services.observability.models import SpanType


@observe(
    name="Call MCP tool",
    description="Call remote MCP server tool to retrieve data or perform actions in external systems, enabling agent to interact with third-party services and resources.",
    type=SpanType.TOOL,
)
async def action_execute_mcp_tool(
    tool_provider: str,
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    observability_context.update_current_span(
        input={
            "MCP provider": tool_provider,
            "MCP tool system name": tool_system_name,
            "Arguments": arguments,
        },
    )

    call_tool_result = await call_mcp_server_tool(
        mcp_server_system_name=tool_provider,
        tool=tool_system_name,
        arguments=arguments,
    )

    # Filter only TextContent instances and combine their text fields into a list
    result_text_contents = [
        c.text for c in call_tool_result.content if isinstance(c, TextContent)
    ]
    result_text_contents_string = json.dumps(result_text_contents)

    result = AgentActionCallResponse(content=result_text_contents_string)

    return result
