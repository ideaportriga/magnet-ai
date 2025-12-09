import time

from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider
from services.observability import observability_context
from services.observability.models import (
    FeatureType,
    LLMType,
    ObservationModelDetails,
    ObservedFeature,
)
from services.observability.utils import get_usage_and_cost_details


async def create_chat_completion(
    *,
    model_system_name: str | None = None,
    llm: str | None,
    messages: list[ChatCompletionMessageParam],
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | None = None,
    related_prompt_template_config: dict | None = None,
) -> ChatCompletion:
    provider_system_name = None

    # Prepare prompt template for traces and metrics
    if related_prompt_template_config:
        observed_feature = ObservedFeature(
            type=FeatureType.PROMPT_TEMPLATE,
            id=related_prompt_template_config.get("id"),
            system_name=related_prompt_template_config.get("system_name"),
            display_name=related_prompt_template_config.get("name"),
            variant=related_prompt_template_config.get("variant"),
        )

        if not model_system_name:
            model_system_name = related_prompt_template_config.get(
                "system_name_for_model"
            )
    else:
        observed_feature = ObservedFeature(
            type=FeatureType.CHAT_COMPLETION,
            system_name=FeatureType.CHAT_COMPLETION.value,
        )

    # Prepare model details for traces and metrics
    call_model = ObservationModelDetails()
    model_config = None
    if model_system_name:
        call_model.update(name=model_system_name)
        model_config = await get_model_by_system_name(model_system_name)
        if model_config:
            model_from_config = model_config.get("ai_model")
            if isinstance(model_from_config, str):
                llm = model_from_config
            display_name = model_config.get("display_name")
            if isinstance(display_name, str):
                call_model.update(display_name=display_name)

            # Use provider_system_name instead of legacy provider field
            provider_system_name_from_config = model_config.get("provider_system_name")
            if isinstance(provider_system_name_from_config, str):
                provider_system_name = provider_system_name_from_config
                call_model.update(provider=provider_system_name)

    # Validate that we have a provider
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    # Prepare provider details for traces and metrics
    # Note: For observability, we'll need to fetch provider info
    # We'll get it when creating the provider instance below
    provider_display_name = provider_system_name  # Default to system_name

    # Prepare model parameters for traces and metrics
    call_model.update(
        parameters={
            "llm": llm,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "response_format": response_format,
            "tools": tools,
        },
    )

    # Prepare input for traces and metrics
    call_input = messages

    with observability_context.observe_feature(observed_feature):
        observability_context.update_current_span(
            name="Generate text",
            description=f'Generating text using chat completion API powered by "{llm}" LLM, provided by {provider_display_name}.',
            model=call_model,
            input=call_input,
            extra_data={
                "tools": tools,
            },
        )

        # Call LLM, get response and calculate duration
        provider = await get_ai_provider(provider_system_name)
        call_start_time = time.time()
        chat_completion = await provider.create_chat_completion(
            messages=messages,
            model=llm,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            model_config=model_config,
        )
        call_end_time = time.time()
        call_duration = call_end_time - call_start_time

        # Prepare usage and cost details for traces and metrics
        call_usage, call_cost = await get_usage_and_cost_details(
            chat_completion.usage, model_system_name
        )

        # Prepare output for traces and metrics
        call_output = {
            "id": chat_completion.id,
            "role": chat_completion.choices[0].message.role,
            "content": chat_completion.choices[0].message.content,
            "tool_calls": [
                {
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in chat_completion.choices[0].message.tool_calls
            ]
            if chat_completion.choices[0].message.tool_calls
            else None,
        }

        # Update current span with usage, cost and output
        observability_context.update_current_span(
            usage_details=call_usage,
            cost_details=call_cost,
            output=call_output,
        )

        # Record chat completion metrics
        observability_context.record_llm_metrics(
            llm_type=LLMType.CHAT_COMPLETION,
            model=call_model,
            duration=call_duration,
            usage=call_usage,
            cost=call_cost,
        )

        return chat_completion


async def create_chat_completion_from_prompt_template(
    prompt_template_config: dict,
    prompt_template_values: dict | None = None,
    additional_messages: list[ChatCompletionMessageParam] | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | None = None,
) -> tuple[ChatCompletion, list[ChatCompletionMessageParam]]:
    system_message: str = prompt_template_config.get("text", "")

    if prompt_template_values:
        for system_message_key, system_message_value in prompt_template_values.items():
            system_message = system_message.replace(
                f"{{{system_message_key}}}",
                str(system_message_value),
            )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message,
        },
        *(additional_messages or []),
    ]

    # Call the LLM
    chat_completion = await create_chat_completion(
        messages=messages,
        llm=prompt_template_config.get("model"),
        temperature=prompt_template_config.get("temperature"),
        top_p=prompt_template_config.get("topP"),
        max_tokens=prompt_template_config.get("maxTokens"),
        response_format=prompt_template_config.get("response_format"),
        model_system_name=prompt_template_config.get("system_name_for_model"),
        tools=tools,
        tool_choice=tool_choice,
        related_prompt_template_config=prompt_template_config,
    )

    return chat_completion, messages


async def get_embeddings(text: str, model_system_name: str):
    llm = None
    provider_system_name = None

    observed_feature = ObservedFeature(
        type=FeatureType.EMBEDDING, system_name=FeatureType.EMBEDDING.value
    )

    # Prepare model details for traces and metrics
    call_model = ObservationModelDetails()
    call_model.update(name=model_system_name)
    model_config = await get_model_by_system_name(model_system_name)
    if model_config:
        llm_from_config = model_config.get("ai_model")
        if llm_from_config and isinstance(llm_from_config, str):
            llm = llm_from_config
        model_display_name = model_config.get("display_name")
        if model_display_name and isinstance(model_display_name, str):
            call_model.update(display_name=model_display_name)

        # Use provider_system_name instead of legacy provider field
        provider_system_name_from_config = model_config.get("provider_system_name")
        if provider_system_name_from_config and isinstance(
            provider_system_name_from_config, str
        ):
            provider_system_name = provider_system_name_from_config
            call_model.update(provider=provider_system_name)
    else:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found",
        )

    # Validate that we have a provider
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    # Prepare provider details for traces and metrics
    provider_display_name = provider_system_name  # Default to system_name

    # Prepare model parameters for traces and metrics
    call_model.update(parameters={"llm": llm})

    # Prepare input for traces and metrics
    call_input = text

    with observability_context.observe_feature(observed_feature):
        observability_context.update_current_span(
            name="Convert text to vector",
            description=f'Creating vector for a given text using "{llm}" LLM, provided by {provider_display_name}.',
            model=call_model,
            input=call_input,
        )

        # Call the LLM
        provider = await get_ai_provider(provider_system_name)
        call_start_time = time.time()
        embeddings = await provider.get_embeddings(text=text, llm=llm)
        call_end_time = time.time()
        call_duration = call_end_time - call_start_time

        # Prepare usage and cost details for traces and metrics
        call_usage, call_cost = await get_usage_and_cost_details(
            embeddings.usage, model_system_name
        )

        # Prepare output for traces and metrics
        call_output = None  # skip vector data

        # Update current span with usage, cost and output
        observability_context.update_current_span(
            usage_details=call_usage,
            cost_details=call_cost,
            output=call_output,
        )

        # Record chat completion metrics
        observability_context.record_llm_metrics(
            llm_type=LLMType.EMBEDDING,
            model=call_model,
            duration=call_duration,
            usage=call_usage,
            cost=call_cost,
        )

        return embeddings.data
