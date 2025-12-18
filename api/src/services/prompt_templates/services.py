from datetime import datetime

from openai.types.chat import ChatCompletionMessageParam

from open_ai.utils_new import (
    create_chat_completion,
    create_chat_completion_from_prompt_template,
)
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.prompt_templates.models import (
    PromptTemplateConfig,
    PromptTemplateExecutionResponse,
)


async def execute_prompt_template(
    *,
    system_name_or_config: str | dict,
    template_variant: str | None = None,
    template_values: dict | None = None,
    template_additional_messages: list[ChatCompletionMessageParam] | None = None,
    config_override: PromptTemplateConfig | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    parallel_tool_calls: bool | None = None,
) -> PromptTemplateExecutionResponse:
    start_time = datetime.now()

    # Get config either directly or by system name
    if isinstance(system_name_or_config, str):
        prompt_template_config = await get_prompt_template_by_system_name_flat(
            system_name_or_config,
            template_variant,
        )
    else:
        prompt_template_config = system_name_or_config

    if config_override:
        chat_completion = await create_chat_completion(
            model_system_name=config_override.model,
            llm=config_override.llm_name,
            messages=config_override.messages or [],
            temperature=config_override.temperature,
            top_p=config_override.top_p,
            max_tokens=config_override.max_tokens,
            response_format=config_override.response_format,
            related_prompt_template_config=prompt_template_config,
            parallel_tool_calls=parallel_tool_calls,
        )
    else:
        chat_completion, _ = await create_chat_completion_from_prompt_template(
            prompt_template_config=prompt_template_config,
            prompt_template_values=template_values,
            additional_messages=template_additional_messages,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
        )

    message = chat_completion.choices[0].message

    tool_calls_data = None
    if message.tool_calls:
        tool_calls_data = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            }
            for tc in message.tool_calls
        ]

    return PromptTemplateExecutionResponse(
        content=str(message.content),
        tool_calls=tool_calls_data,
        usage={
            "prompt_tokens": chat_completion.usage.prompt_tokens
            if chat_completion.usage
            else 0,
            "completion_tokens": chat_completion.usage.completion_tokens
            if chat_completion.usage
            else 0,
            "total_tokens": chat_completion.usage.total_tokens
            if chat_completion.usage
            else 0,
        },
        latency=(datetime.now() - start_time).total_seconds() * 1000,
        cost=chat_completion.cost_details.total if hasattr(chat_completion, 'cost_details') and chat_completion.cost_details else None,
    )
