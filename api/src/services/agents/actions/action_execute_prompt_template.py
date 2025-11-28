from services.agents.models import AgentActionCallResponse
from services.observability import observability_context, observe
from services.observability.models import SpanType
from services.prompt_templates import execute_prompt_template


@observe(
    name="Call prompt template",
    description="Call prompt template to generate a response based on user's message.",
    type=SpanType.TOOL,
)
async def action_execute_prompt_template(
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    user_message = arguments.get("userMessage")

    assert user_message and isinstance(user_message, str), (
        "Cannot call Prompt Template - user message is missing"
    )

    observability_context.update_current_span(
        input={
            "Prompt template system name": tool_system_name,
            "User message": user_message,
        },
    )

    prompt_template_execute_result = await execute_prompt_template(
        system_name_or_config=tool_system_name,
        template_additional_messages=[
            {
                "role": "user",
                "content": user_message,
            },
        ],
    )

    result = AgentActionCallResponse(
        content=prompt_template_execute_result.content,
    )

    return result
