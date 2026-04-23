import json
import time
from collections.abc import AsyncIterator
from typing import BinaryIO

from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

from open_ai.models import ChatCompletionWithMetrics
from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider
from services.ai_services.router import get_model_system_name_by_deployment_id
from services.observability import observability_context
from services.observability.models import (
    FeatureType,
    LLMType,
    ObservabilityLevel,
    ObservationModelDetails,
    ObservedFeature,
)
from services.observability.utils import get_usage_and_cost_details


def _get_observability_level_from_config(config: dict | None) -> ObservabilityLevel:
    """Extract observability level from prompt template config."""
    if not config:
        return ObservabilityLevel.FULL

    level_value = config.get("observability_level")
    if level_value is None:
        return ObservabilityLevel.FULL

    try:
        return ObservabilityLevel(level_value)
    except ValueError:
        return ObservabilityLevel.FULL


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
    tool_choice: str | dict | None = None,
    related_prompt_template_config: dict | None = None,
    parallel_tool_calls: bool | None = None,
) -> ChatCompletionWithMetrics:
    provider_system_name = None

    # Prepare prompt template for traces and metrics
    if related_prompt_template_config:
        # Get observability level from prompt template config
        observability_level = _get_observability_level_from_config(
            related_prompt_template_config
        )

        observed_feature = ObservedFeature(
            type=FeatureType.PROMPT_TEMPLATE,
            id=related_prompt_template_config.get("id"),
            system_name=related_prompt_template_config.get("system_name"),
            display_name=related_prompt_template_config.get("name"),
            variant=related_prompt_template_config.get("variant"),
            observability_level=observability_level,
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

    with observability_context.observe_feature(observed_feature) as instance_id:
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

        # Enrich call_model with provider-level observability details
        otel_system = getattr(provider, "otel_gen_ai_system", None)
        if otel_system:
            call_model.update(otel_gen_ai_system=otel_system)
        provider_label = getattr(provider, "config", {}).get("label")
        if provider_label:
            call_model.update(provider_display_name=provider_label)

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
            parallel_tool_calls=parallel_tool_calls,
        )
        call_end_time = time.time()
        call_duration = call_end_time - call_start_time

        # Detect if a fallback model handled the request.
        # When the Router is used, _hidden_params["model_id"] identifies
        # which deployment actually served the request. If it maps to a
        # different system_name than the one we requested, a fallback occurred.
        actual_model_system_name = model_system_name
        if (
            hasattr(chat_completion, "_hidden_params")
            and chat_completion._hidden_params
        ):
            hidden = chat_completion._hidden_params
            deployment_model_id = hidden.get("model_id")
            if deployment_model_id:
                resolved = get_model_system_name_by_deployment_id(deployment_model_id)
                if resolved and resolved != model_system_name:
                    actual_model_system_name = resolved

                    # Update model details for traces/metrics with actual model info
                    actual_config = await get_model_by_system_name(
                        actual_model_system_name
                    )
                    actual_display = (
                        actual_config.get("display_name")
                        if actual_config
                        else actual_model_system_name
                    )
                    actual_provider = (
                        actual_config.get("provider_system_name")
                        if actual_config
                        else None
                    )
                    actual_llm = (
                        actual_config.get("ai_model") if actual_config else None
                    )

                    call_model.update(
                        name=actual_model_system_name,
                        display_name=f"{actual_display} (fallback)",
                    )
                    if actual_provider:
                        call_model.update(provider=actual_provider)
                        # Update provider-level details for the fallback provider
                        try:
                            fb_provider = await get_ai_provider(actual_provider)
                            fb_otel = getattr(fb_provider, "otel_gen_ai_system", None)
                            if fb_otel:
                                call_model.update(otel_gen_ai_system=fb_otel)
                            fb_label = getattr(fb_provider, "config", {}).get("label")
                            if fb_label:
                                call_model.update(provider_display_name=fb_label)
                        except Exception:
                            pass  # Don't fail the request over observability

                    # Update parameters.llm to the actual fallback model
                    if actual_llm:
                        params = call_model.get("parameters") or {}
                        params["llm"] = actual_llm
                        call_model.update(parameters=params)

                    # Update the span with fallback info
                    observability_context.update_current_span(
                        model=call_model,
                        extra_data={
                            "fallback": True,
                            "original_model": model_system_name,
                            "actual_model": actual_model_system_name,
                        },
                    )

        # Prepare usage and cost details — use the actual model for correct pricing
        call_usage, call_cost = await get_usage_and_cost_details(
            chat_completion.usage, actual_model_system_name
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

        result = ChatCompletionWithMetrics(
            **chat_completion.model_dump(),
            usage_details=call_usage,
            cost_details=call_cost,
            feature_instance_id=instance_id,
        )

        return result


async def create_chat_completion_from_prompt_template(
    prompt_template_config: dict,
    prompt_template_values: dict | None = None,
    additional_messages: list[ChatCompletionMessageParam] | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    parallel_tool_calls: bool | None = None,
) -> tuple[ChatCompletionWithMetrics, list[ChatCompletionMessageParam]]:
    system_message: str = prompt_template_config.get("text", "")
    response_format: dict | None = prompt_template_config.get("response_format")

    if prompt_template_values:
        for system_message_key, system_message_value in prompt_template_values.items():
            system_message = system_message.replace(
                f"{{{system_message_key}}}",
                str(system_message_value),
            )
        if response_format is not None:
            format_str = json.dumps(response_format)
            for key, value in prompt_template_values.items():
                format_str = format_str.replace(f"{{{key}}}", str(value))
            try:
                response_format = json.loads(format_str)
            except json.JSONDecodeError:
                pass  # Keep original if substitution produced invalid JSON

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": system_message or "",
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
        response_format=response_format,
        model_system_name=prompt_template_config.get("system_name_for_model"),
        tools=tools,
        tool_choice=tool_choice,
        related_prompt_template_config=prompt_template_config,
        parallel_tool_calls=parallel_tool_calls,
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

        # Enrich call_model with provider-level observability details
        otel_system = getattr(provider, "otel_gen_ai_system", None)
        if otel_system:
            call_model.update(otel_gen_ai_system=otel_system)
        provider_label = getattr(provider, "config", {}).get("label")
        if provider_label:
            call_model.update(provider_display_name=provider_label)

        call_start_time = time.time()
        embeddings = await provider.get_embeddings(
            text=text,
            llm=llm,
            model_config=model_config,
        )
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


async def create_chat_completion_stream(
    *,
    model_system_name: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    parallel_tool_calls: bool | None = None,
) -> AsyncIterator[ChatCompletionChunk]:
    """
    Stream chat completion chunks with observability.

    Yields ChatCompletionChunk objects. The final chunk includes usage
    information when the provider supports stream_options.include_usage.

    Usage:
        async for chunk in create_chat_completion_stream(
            model_system_name="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        ):
            content = chunk.choices[0].delta.content or ""
            print(content, end="")
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    call_start_time = time.time()

    async for chunk in provider.create_chat_completion_stream(
        messages=messages,
        model=llm,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        model_config=model_config,
        parallel_tool_calls=parallel_tool_calls,
    ):
        yield chunk

    call_duration = time.time() - call_start_time

    # Record streaming metrics via observability
    call_model = ObservationModelDetails()
    call_model.update(
        name=model_system_name,
        display_name=model_config.get("display_name"),
        provider=provider_system_name,
        parameters={"llm": llm, "streaming": True},
    )
    otel_system = getattr(provider, "otel_gen_ai_system", None)
    if otel_system:
        call_model.update(otel_gen_ai_system=otel_system)

    observability_context.record_llm_metrics(
        llm_type=LLMType.CHAT_COMPLETION,
        model=call_model,
        duration=call_duration,
        usage=None,
        cost=None,
    )


async def transcribe(
    *,
    model_system_name: str,
    file: BinaryIO,
    language: str | None = None,
    prompt: str | None = None,
    response_format: str | None = None,
    timestamp_granularities: list[str] | None = None,
):
    """
    Transcribe audio using the provider configured for the given model.

    Args:
        model_system_name: System name of the STT model in the database
        file: Audio file binary stream
        language: Language hint (ISO 639-1)
        prompt: Optional prompt to guide transcription
        response_format: Output format (json, text, srt, verbose_json, vtt)
        timestamp_granularities: Timestamp detail levels

    Returns:
        TranscriptionResponse with text, segments, etc.
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    return await provider.transcribe(
        file=file,
        model=llm,
        language=language,
        prompt=prompt,
        response_format=response_format,
        timestamp_granularities=timestamp_granularities,
    )


async def text_to_speech(
    *,
    model_system_name: str,
    input: str,
    voice: str | None = None,
    response_format: str | None = None,
    speed: float | None = None,
) -> bytes:
    """
    Generate speech audio using the provider configured for the given model.

    Args:
        model_system_name: System name of the TTS model in the database
        input: Text to convert to speech
        voice: Voice to use (provider-specific)
        response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
        speed: Speech speed multiplier

    Returns:
        Raw audio bytes
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    return await provider.speech(
        input=input,
        model=llm,
        voice=voice,
        response_format=response_format,
        speed=speed,
    )


async def create_response(
    *,
    model_system_name: str,
    input: str | list,
    instructions: str | None = None,
    tools: list | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    tool_choice: str | dict | None = None,
    previous_response_id: str | None = None,
    background: bool | None = None,
    reasoning: dict | None = None,
    text_format: dict | type | None = None,
    **kwargs,
):
    """
    Create a response using the Responses API.

    Supports OpenAI Responses API, GPT-5 Codex (background=True),
    built-in web search / file search tools, and stateful conversations
    via previous_response_id.

    LiteLLM automatically translates Responses API calls to Chat Completions
    for providers that don't natively support it (e.g., Anthropic, Gemini).

    Args:
        model_system_name: System name of the model in the database
        input: Prompt string or structured input list
        instructions: System instructions
        tools: Tool definitions (web_search, file_search, function, etc.)
        max_output_tokens: Maximum output tokens
        temperature: Sampling temperature
        top_p: Top-p sampling
        tool_choice: Tool choice setting
        previous_response_id: ID of previous response for multi-turn
        background: Run in background mode (GPT-5 Codex)
        reasoning: Reasoning configuration (e.g., {"effort": "high"})
        text_format: Structured output format (Pydantic model or dict)
        **kwargs: Additional litellm.aresponses parameters

    Returns:
        ResponsesAPIResult with id, output_text, model, status, usage, raw
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    return await provider.create_response(
        input=input,
        model=llm,
        instructions=instructions,
        tools=tools,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        tool_choice=tool_choice,
        previous_response_id=previous_response_id,
        background=background,
        reasoning=reasoning,
        text_format=text_format,
        model_config=model_config,
        **kwargs,
    )


async def create_response_stream(
    *,
    model_system_name: str,
    input: str | list,
    instructions: str | None = None,
    tools: list | None = None,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    tool_choice: str | dict | None = None,
    previous_response_id: str | None = None,
    reasoning: dict | None = None,
    text_format: dict | type | None = None,
    **kwargs,
) -> AsyncIterator:
    """
    Stream a Responses API response.

    Yields streaming events from the Responses API. Each event is a
    ResponsesAPIStreamingResponse with type, data, etc.

    Usage:
        async for event in create_response_stream(
            model_system_name="gpt-4.1",
            input="Explain quantum computing",
        ):
            print(event)
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    async for event in provider.create_response_stream(
        input=input,
        model=llm,
        instructions=instructions,
        tools=tools,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        tool_choice=tool_choice,
        previous_response_id=previous_response_id,
        reasoning=reasoning,
        text_format=text_format,
        model_config=model_config,
        **kwargs,
    ):
        yield event


async def generate_image(
    *,
    model_system_name: str,
    prompt: str,
    n: int = 1,
    size: str | None = None,
    quality: str | None = None,
    style: str | None = None,
    response_format: str | None = None,
):
    """
    Generate images using the provider configured for the given model.

    Supports OpenAI DALL-E, Azure OpenAI, Vertex AI Imagen, Bedrock, etc.

    Args:
        model_system_name: System name of the image model in the database
        prompt: Text description of the image to generate
        n: Number of images to generate
        size: Image size (e.g., "1024x1024", "1792x1024")
        quality: Image quality ("standard", "hd")
        style: Image style ("vivid", "natural")
        response_format: Output format ("url" or "b64_json")

    Returns:
        ImageGenerationResult with images list, model, raw response
    """
    model_config = await get_model_by_system_name(model_system_name)
    if not model_config:
        raise LookupError(
            f"Model configuration with system_name '{model_system_name}' was not found"
        )

    llm = model_config.get("ai_model")
    provider_system_name = model_config.get("provider_system_name")
    if not provider_system_name:
        raise ValueError(
            f"Model '{model_system_name}' does not have a provider_system_name configured"
        )

    provider = await get_ai_provider(provider_system_name)

    return await provider.generate_image(
        prompt=prompt,
        model=llm,
        n=n,
        size=size,
        quality=quality,
        style=style,
        response_format=response_format,
    )
