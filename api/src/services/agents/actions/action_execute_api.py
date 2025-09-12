from services.agents.models import AgentActionCallResponse
from services.api_tools.flow_execute import api_tool_execute
from services.api_tools.types import ApiToolExecute, ApiToolExecuteInputParams
from services.observability import observability_context, observe
from services.observability.models import SpanType


@observe(
    name="Call API",
    description="Call external API to retrieve data or perform actions in external systems, enabling agent to interact with third-party services and resources.",
    type=SpanType.TOOL,
)
async def action_execute_api(
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    input_params = ApiToolExecuteInputParams(**arguments)

    observability_context.update_current_span(
        input={
            "API tool system name": tool_system_name,
            "Input params": input_params.model_dump(),
        },
    )

    api_tool_execute_result = await api_tool_execute(
        ApiToolExecute(
            system_name=tool_system_name, input_params=input_params, variables=variables
        )
    )

    result = AgentActionCallResponse(
        content=api_tool_execute_result.content,  # TODO - could it be useful to also add status code here?
        verbose_details=api_tool_execute_result.model_dump(),
    )

    return result
