"""
Base LiteLLM Provider with routing_config support.

This module provides a base class for AI providers that use LiteLLM,
with built-in support for:
- In-memory response caching
- Automatic retries with backoff
- Fallback models
- Rate limiting awareness
- Unified interface across different AI providers

Supported LiteLLM model prefixes:
- openai/ - OpenAI models
- azure/ - Azure OpenAI deployments
- azure_ai/ - Azure AI Inference
- groq/ - Groq models
- anthropic/ - Anthropic Claude
- gemini/ - Google Gemini
- bedrock/ - AWS Bedrock
- together_ai/ - Together AI
- ollama/ - Local Ollama
- And many more...
"""

import logging
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any, BinaryIO, cast

import litellm
from litellm.caching import Cache
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
)

from models import DocumentSearchResult
from services.ai_services.cache import response_cache
from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import (
    EmbeddingResponse,
    ImageGenerationResult,
    ModelUsage,
    RerankResponse,
    ResponsesAPIResult,
    RoutingConfig,
    TranscriptionResponse,
)

logger = logging.getLogger(__name__)

# Suppress verbose litellm logging
litellm.suppress_debug_info = True

# Silently drop parameters that a model does not support instead of raising
# a hard error.  This handles edge-cases like max_tokens being rejected by
# newer OpenAI models that only accept max_completion_tokens — litellm will
# simply omit unsupported params from the request.
litellm.drop_params = True

# Configure LiteLLM in-memory cache globally
litellm.cache = Cache(type="local")  # In-memory cache
litellm.enable_cache = (
    False  # Disabled by default, enabled per-request via routing_config
)


class BaseLiteLLMProvider(AIProviderInterface):
    """
    Base class for LiteLLM-based providers.

    Provides unified support for:
    - Chat completions with routing_config
    - Embeddings
    - Reranking
    - Batch processing
    - In-memory caching
    - Automatic fallbacks

    Subclasses should set:
    - litellm_provider: The LiteLLM provider prefix (e.g., "openai", "azure", "groq")
    """

    # Override in subclass to set the LiteLLM provider prefix
    litellm_provider: str = ""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the provider with configuration.

        Args:
            config: Provider configuration containing:
                - connection: API keys, endpoints, etc.
                - defaults: Default model parameters
                - type: Provider type for determining litellm prefix
        """
        self.config = config
        self.connection = config.get("connection", {})
        defaults = config.get("defaults", {})

        # Store connection params
        self.api_key = self.connection.get("api_key")
        self.endpoint = self.connection.get("endpoint")
        self.api_version = self.connection.get("api_version")

        # Store defaults
        self.model_default = defaults.get("model")
        self.temperature_default = defaults.get("temperature")
        self.top_p_default = defaults.get("top_p")
        self.max_tokens_default = defaults.get("max_tokens")

        # OpenTelemetry system name for tracing
        self.otel_gen_ai_system = config.get("otel_gen_ai_system")

    def _get_model_name(self, model: str) -> str:
        """
        Get the full model name with LiteLLM provider prefix.

        Always prepends the provider prefix if the model doesn't already
        start with it. Model names can contain '/' as part of the identifier
        (e.g. 'qwen/qwen3-4b-2507' from LM Studio) — this is NOT a provider prefix.
        """
        if self.litellm_provider:
            if not model.startswith(f"{self.litellm_provider}/"):
                return f"{self.litellm_provider}/{model}"
        return model

    def _build_litellm_params(self) -> dict[str, Any]:
        """Build common LiteLLM parameters from connection config."""
        params: dict[str, Any] = {}

        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint
        if self.api_version:
            params["api_version"] = self.api_version

        return params

    def _extract_routing_config(self, model_config: dict | None) -> RoutingConfig:
        """Extract routing_config from model_config and return typed RoutingConfig."""
        if not model_config:
            return RoutingConfig()
        raw = model_config.get("routing_config") or {}
        return RoutingConfig.from_dict(raw)

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> ChatCompletion:
        """
        Create chat completion using LiteLLM with routing_config support.

        The routing_config from model_config enables:
        - cache_enabled/cache_ttl: In-memory response caching
        - fallback_models: Automatic failover to other models
        - num_retries: Retry with exponential backoff
        - timeout: Request timeout
        """
        model = model or self.model_default
        if not model:
            raise ValueError("Model must be specified")

        routing_config = self._extract_routing_config(model_config)

        params = self._build_completion_params(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            model_config=model_config,
            parallel_tool_calls=parallel_tool_calls,
            routing_config=routing_config,
        )

        response = await self._execute_completion(params, routing_config, model_config)

        # Zero out usage for cached responses to avoid double billing
        # LiteLLM stores cache_hit in _hidden_params
        if hasattr(response, "_hidden_params") and response._hidden_params.get(
            "cache_hit"
        ):
            if hasattr(response, "usage") and response.usage:
                response.usage.prompt_tokens = 0
                response.usage.completion_tokens = 0
                response.usage.total_tokens = 0

        return cast(ChatCompletion, response)

    async def create_chat_completion_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        Stream chat completion chunks using LiteLLM.

        Yields ChatCompletionChunk objects. The final chunk includes usage
        information when stream_options={"include_usage": True}.
        """
        model = model or self.model_default
        if not model:
            raise ValueError("Model must be specified")

        routing_config = self._extract_routing_config(model_config)

        params = self._build_completion_params(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            model_config=model_config,
            parallel_tool_calls=parallel_tool_calls,
            routing_config=routing_config,
        )

        # Enable streaming
        params["stream"] = True
        params["stream_options"] = {"include_usage": True}

        response = await self._execute_stream(params, routing_config, model_config)
        async for chunk in response:
            yield chunk

    async def _execute_stream(
        self,
        params: dict[str, Any],
        routing_config: RoutingConfig,
        model_config: dict | None,
    ) -> Any:
        """Execute a streaming LLM call.

        Uses global Router for fallback support when fallback_models are configured,
        otherwise calls litellm.acompletion directly.

        Subclasses can override this to use their own Router instance.
        """
        use_router = bool(routing_config.fallback_models)

        if use_router:
            from services.ai_services.router import get_router

            router = await get_router()
            model_system_name = (model_config or {}).get("system_name")
            if not model_system_name:
                logger.warning(
                    "No system_name in model_config, falling back to direct litellm call for stream"
                )
                return await litellm.acompletion(**params)
            else:
                router_params = {
                    k: v
                    for k, v in params.items()
                    if k not in ("api_key", "api_base", "api_version")
                }
                router_params["model"] = model_system_name
                return await router.acompletion(**router_params)
        else:
            return await litellm.acompletion(**params)

    def _build_completion_params(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None,
        response_format: dict | None,
        tools: list[dict] | None,
        tool_choice: str | dict | None,
        model_config: dict | None,
        parallel_tool_calls: bool | None,
        routing_config: RoutingConfig,
    ) -> dict[str, Any]:
        """Build the full parameter dict for a chat completion call.

        Separated from execution so subclasses can reuse param-building
        while providing their own execution strategy (e.g. own Router).
        """
        full_model = self._get_model_name(model)
        temperature = (
            temperature if temperature is not None else self.temperature_default
        )
        top_p = top_p if top_p is not None else self.top_p_default
        max_tokens = max_tokens or self.max_tokens_default

        # Build request parameters
        params = self._build_litellm_params()
        params["model"] = full_model
        params["messages"] = messages

        # Get supported parameters for this model from LiteLLM
        try:
            # Remove provider prefix for param lookup (e.g., "openai/gpt-4o" -> "gpt-4o")
            model_for_lookup = (
                full_model.split("/", 1)[-1] if "/" in full_model else full_model
            )
            supported_params = set(
                litellm.get_supported_openai_params(model_for_lookup) or []
            )
        except Exception:
            # Fallback: assume all standard params are supported
            supported_params = {
                "temperature",
                "top_p",
                "max_tokens",
                "max_completion_tokens",
            }

        # Check if reasoning model (for reasoning_effort parameter)
        is_reasoning_model = model_config and model_config.get("reasoning")

        # Add optional parameters based on model support
        if temperature is not None:
            if is_reasoning_model:
                # Reasoning models use reasoning_effort instead of temperature
                params["reasoning_effort"] = (model_config or {}).get(
                    "reasoning_effort", "medium"
                )
            elif "temperature" in supported_params:
                params["temperature"] = temperature

        if top_p is not None and "top_p" in supported_params:
            params["top_p"] = top_p

        if max_tokens is not None:
            # Prefer max_completion_tokens for newer models that support it.
            # litellm reports both params as supported for most models, but newer
            # OpenAI models (o3-mini, o4-mini, gpt-5, etc.) reject max_tokens.
            # Reasoning models always need max_completion_tokens.
            if "max_completion_tokens" in supported_params:
                params["max_completion_tokens"] = max_tokens
            elif "max_tokens" in supported_params:
                params["max_tokens"] = max_tokens
            else:
                # Neither explicitly listed — default to max_completion_tokens
                params["max_completion_tokens"] = max_tokens

        if response_format is not None:
            params["response_format"] = self._transform_response_format(response_format)

        if tools is not None:
            params["tools"] = tools

        if tool_choice is not None:
            params["tool_choice"] = tool_choice

        if parallel_tool_calls is not None and tools:
            params["parallel_tool_calls"] = parallel_tool_calls

        # Apply routing config
        if routing_config.timeout:
            params["timeout"] = routing_config.timeout

        # Use 'is not None' so that num_retries=0 is properly passed
        # (0 means no retries — try once, then fallback immediately)
        if routing_config.num_retries is not None:
            params["num_retries"] = routing_config.num_retries

        if routing_config.retry_after is not None:
            params["retry_after"] = routing_config.retry_after

        # Extra LiteLLM params from routing_config
        if routing_config.litellm_params:
            params.update(routing_config.litellm_params)

        # Enable LiteLLM built-in cache if configured (not for tool calls)
        if routing_config.cache_enabled and not tools:
            params["caching"] = True
            params["cache"] = {"ttl": routing_config.cache_ttl}

        return params

    async def _execute_completion(
        self,
        params: dict[str, Any],
        routing_config: RoutingConfig,
        model_config: dict | None,
    ) -> ChatCompletion:
        """Execute the actual LLM call.

        Uses global Router for fallback support when fallback_models are configured,
        otherwise calls litellm.acompletion directly.

        Subclasses can override this to use their own Router instance.
        """
        use_router = bool(routing_config.fallback_models)

        if use_router:
            # Use Router for fallback support — the Router knows all model configs
            # (API keys, endpoints, etc.) and can properly resolve system_names.
            from services.ai_services.router import get_router

            router = await get_router()

            # Build router params — use the model's system_name (not the litellm model name)
            # because the Router maps system_names to actual model deployments.
            model_system_name = (model_config or {}).get("system_name")
            if not model_system_name:
                # Fallback to direct call if we don't have system_name
                logger.warning(
                    "No system_name in model_config, falling back to direct litellm call"
                )
                response = await litellm.acompletion(**params)
            else:
                # Build router-compatible params (without provider-specific api_key/api_base)
                router_params = {
                    k: v
                    for k, v in params.items()
                    if k not in ("api_key", "api_base", "api_version")
                }
                router_params["model"] = model_system_name
                response = await router.acompletion(**router_params)
        else:
            response = await litellm.acompletion(**params)

        return cast(ChatCompletion, response)

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        """Get embeddings using LiteLLM."""
        if llm is None:
            raise ValueError("Model name must be provided")

        full_model = self._get_model_name(llm)
        params = self._build_litellm_params()
        params["model"] = full_model
        params["input"] = [text]

        response = await litellm.aembedding(**params)

        return EmbeddingResponse(
            data=response.data[0]["embedding"],
            usage=ModelUsage(
                input_units="tokens",
                input=response.usage.prompt_tokens,
                total=response.usage.total_tokens,
            ),
        )

    async def rerank(
        self,
        query: str,
        documents: DocumentSearchResult,
        llm: str,
        top_n: int,
        truncation: bool | None = None,
    ) -> RerankResponse:
        """Rerank documents using LiteLLM."""
        full_model = self._get_model_name(llm)
        doc_texts = [doc.content or "" for doc in documents]

        response = await litellm.arerank(
            model=full_model,
            query=query,
            documents=doc_texts,
            top_n=top_n,
        )

        usage = None
        if hasattr(response, "usage") and response.usage:
            usage = ModelUsage(
                input_units="tokens",
                input=getattr(response.usage, "prompt_tokens", 0),
                total=getattr(response.usage, "total_tokens", 0),
            )

        scores: dict[int, float] = {}
        if hasattr(response, "results"):
            for result in response.results:
                scores[result.index] = result.relevance_score

        reranked_documents: DocumentSearchResult = []
        for idx, doc in enumerate(documents):
            new_score = scores.get(idx)
            if new_score is not None:
                doc.score = Decimal(str(new_score))
            doc.original_index = idx
            reranked_documents.append(doc)

        return RerankResponse(data=reranked_documents, usage=usage)

    async def batch_completions(
        self,
        requests: list[dict[str, Any]],
        model_config: dict | None = None,
    ) -> list[ChatCompletion]:
        """Execute multiple completion requests in parallel."""
        batch_params = []
        for req in requests:
            model = req.get("model", self.model_default)
            params = {
                "model": self._get_model_name(model),
                "messages": req["messages"],
                **self._build_litellm_params(),
            }
            if "temperature" in req:
                params["temperature"] = req["temperature"]
            if "top_p" in req:
                params["top_p"] = req["top_p"]
            if "max_tokens" in req:
                params["max_tokens"] = req["max_tokens"]
            if "response_format" in req:
                params["response_format"] = self._transform_response_format(
                    req["response_format"]
                )
            if "tools" in req:
                params["tools"] = req["tools"]
            if "tool_choice" in req:
                params["tool_choice"] = req["tool_choice"]
            batch_params.append(params)

        responses = await litellm.abatch_completion(batch_params)
        return [cast(ChatCompletion, r) for r in responses]

    def _transform_response_format(self, response_format: dict | None) -> dict | None:
        """Transform response format for LiteLLM compatibility.

        For json_schema responses with ``strict: true`` OpenAI requires:
        - Every ``type: "object"`` node to have ``"additionalProperties": false``
        - Every ``type: "object"`` with ``properties`` to list **all** property
          keys in ``required``
        - No unsupported ``format`` values (e.g. ``"uri"``)

        Instead of rejecting the request we automatically patch the schema so
        that callers don't have to remember all these constraints.
        """
        if response_format is None:
            return None

        if response_format.get("type") == "json_schema":
            json_schema = response_format.get("json_schema", {})
            schema = json_schema.get("schema")
            if isinstance(schema, str):
                import json

                schema = json.loads(schema)
                json_schema["schema"] = schema

            # Auto-fix schema for OpenAI strict mode compliance
            if isinstance(schema, dict) and json_schema.get("strict"):
                self._fix_schema_for_strict_mode(schema)

            return response_format

        if response_format.get("type") == "json_object":
            return {"type": "json_object"}

        return response_format

    # Formats that OpenAI's strict mode does not support
    _UNSUPPORTED_FORMATS = {"uri", "uri-reference", "iri", "iri-reference"}

    # JSON Schema keywords not supported by OpenAI strict mode
    _UNSUPPORTED_SCHEMA_KEYS = {"patternProperties", "minProperties", "maxProperties"}

    def _fix_schema_for_strict_mode(self, schema: dict) -> None:
        """Recursively patch a JSON Schema dict so it satisfies OpenAI strict mode.

        Mutations applied in-place:
        1. ``additionalProperties: false`` on every ``type: "object"``.
        2. ``required`` set to all keys of ``properties`` when missing or incomplete.
        3. Unsupported ``format`` values (e.g. ``uri``) are removed.
        4. Unsupported schema keywords (e.g. ``patternProperties``) are removed.
        5. Objects without ``properties`` get an empty ``properties`` + empty ``required``.
        """
        if not isinstance(schema, dict):
            return

        # Remove unsupported schema keywords (e.g. patternProperties)
        for unsupported_key in self._UNSUPPORTED_SCHEMA_KEYS:
            if unsupported_key in schema:
                logger.debug(
                    "Removing unsupported schema key '%s' from schema",
                    unsupported_key,
                )
                del schema[unsupported_key]

        # Fix object nodes
        if schema.get("type") == "object":
            schema.setdefault("additionalProperties", False)
            props = schema.get("properties")
            if props and isinstance(props, dict):
                schema["required"] = list(props.keys())
            else:
                # Objects must have explicit properties in strict mode
                schema.setdefault("properties", {})
                schema["required"] = list(schema["properties"].keys())

        # Remove unsupported format values
        fmt = schema.get("format")
        if fmt and fmt in self._UNSUPPORTED_FORMATS:
            logger.debug("Removing unsupported format '%s' from schema", fmt)
            del schema["format"]

        # Recurse into properties
        for prop_schema in (schema.get("properties") or {}).values():
            self._fix_schema_for_strict_mode(prop_schema)

        # Recurse into array items
        items = schema.get("items")
        if isinstance(items, dict):
            self._fix_schema_for_strict_mode(items)

        # Recurse into anyOf / oneOf / allOf
        for key in ("anyOf", "oneOf", "allOf"):
            for sub in schema.get(key) or []:
                self._fix_schema_for_strict_mode(sub)

        # Recurse into $defs / definitions
        for key in ("$defs", "definitions"):
            for sub in (schema.get(key) or {}).values():
                self._fix_schema_for_strict_mode(sub)

    # ------------------------------------------------------------------
    # STT / TTS methods
    # ------------------------------------------------------------------

    async def transcribe(
        self,
        file: BinaryIO,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str | None = None,
        timestamp_granularities: list[str] | None = None,
    ) -> TranscriptionResponse:
        """Transcribe audio using LiteLLM atranscription()."""
        model = model or self.config.get("defaults", {}).get("stt_model")
        if not model:
            raise ValueError("STT model must be specified")

        full_model = self._get_model_name(model)
        params: dict[str, Any] = self._build_litellm_params()
        params["model"] = full_model
        params["file"] = file

        if language:
            params["language"] = language
        if prompt:
            params["prompt"] = prompt
        if response_format:
            params["response_format"] = response_format
        if timestamp_granularities:
            params["timestamp_granularities"] = timestamp_granularities

        response = await litellm.atranscription(**params)

        return TranscriptionResponse(
            text=getattr(response, "text", str(response)),
            language=getattr(response, "language", None),
            duration=getattr(response, "duration", None),
            segments=[s.model_dump() for s in response.segments]
            if hasattr(response, "segments") and response.segments
            else None,
            words=[w.model_dump() for w in response.words]
            if hasattr(response, "words") and response.words
            else None,
        )

    async def speech(
        self,
        input: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,
        speed: float | None = None,
    ) -> bytes:
        """Generate speech audio using LiteLLM aspeech()."""
        model = model or self.config.get("defaults", {}).get("tts_model")
        if not model:
            raise ValueError("TTS model must be specified")

        full_model = self._get_model_name(model)
        params: dict[str, Any] = {
            "model": full_model,
            "input": input,
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint
        if voice:
            params["voice"] = voice
        if response_format:
            params["response_format"] = response_format
        if speed:
            params["speed"] = speed

        response = await litellm.aspeech(**params)
        # response is HttpxBinaryResponseContent
        return response.read()

    # ------------------------------------------------------------------
    # Responses API (Phase 9)
    # ------------------------------------------------------------------

    async def create_response(
        self,
        input: str | list,
        model: str | None = None,
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
        model_config: dict | None = None,
        **kwargs,
    ) -> ResponsesAPIResult:
        """
        Create a response using the Responses API (litellm.aresponses).

        Supports:
        - OpenAI /v1/responses endpoint (GPT-4.1, GPT-5, Codex, etc.)
        - Built-in web search, file search tools
        - Stateful conversations via previous_response_id
        - Background mode for long-running tasks (Codex)
        - LiteLLM translates to Chat Completions for unsupported providers
        """
        model = model or self.model_default
        if not model:
            raise ValueError("Model must be specified")

        full_model = self._get_model_name(model)

        params: dict[str, Any] = {
            "model": full_model,
            "input": input,
        }

        # Add connection params
        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint

        # Optional parameters
        if instructions is not None:
            params["instructions"] = instructions
        if tools is not None:
            params["tools"] = tools
        if max_output_tokens is not None:
            params["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if previous_response_id is not None:
            params["previous_response_id"] = previous_response_id
        if background is not None:
            params["background"] = background
        if reasoning is not None:
            params["reasoning"] = reasoning
        if text_format is not None:
            params["text_format"] = text_format

        # Pass through any additional kwargs (extra_headers, metadata, etc.)
        params.update(kwargs)

        # Apply routing config timeout if present
        routing_config = self._extract_routing_config(model_config)
        if routing_config.timeout:
            params["timeout"] = routing_config.timeout

        response = await litellm.aresponses(**params)

        # Extract output text from the response
        output_text = ""
        if hasattr(response, "output") and response.output:
            text_parts = []
            for item in response.output:
                if hasattr(item, "content") and item.content:
                    for content_block in item.content:
                        if hasattr(content_block, "text"):
                            text_parts.append(content_block.text)
                elif isinstance(item, dict):
                    # Dict-form output item
                    for content_block in item.get("content", []):
                        if isinstance(content_block, dict) and "text" in content_block:
                            text_parts.append(content_block["text"])
            output_text = "\n".join(text_parts)

        # Extract usage
        usage = None
        if hasattr(response, "usage") and response.usage:
            usage = ModelUsage(
                input_units="tokens",
                input=getattr(response.usage, "input_tokens", 0) or 0,
                total=(
                    (getattr(response.usage, "input_tokens", 0) or 0)
                    + (getattr(response.usage, "output_tokens", 0) or 0)
                ),
            )

        return ResponsesAPIResult(
            id=getattr(response, "id", ""),
            output_text=output_text,
            model=getattr(response, "model", full_model),
            status=getattr(response, "status", None),
            usage=usage,
            raw=response,
        )

    async def create_response_stream(
        self,
        input: str | list,
        model: str | None = None,
        instructions: str | None = None,
        tools: list | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        tool_choice: str | dict | None = None,
        previous_response_id: str | None = None,
        reasoning: dict | None = None,
        text_format: dict | type | None = None,
        model_config: dict | None = None,
        **kwargs,
    ):
        """
        Stream a Responses API response.

        Yields streaming events from litellm.aresponses(stream=True).
        Each event is a ResponsesAPIStreamingResponse.
        """
        model = model or self.model_default
        if not model:
            raise ValueError("Model must be specified")

        full_model = self._get_model_name(model)

        params: dict[str, Any] = {
            "model": full_model,
            "input": input,
            "stream": True,
        }

        # Add connection params
        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint

        if instructions is not None:
            params["instructions"] = instructions
        if tools is not None:
            params["tools"] = tools
        if max_output_tokens is not None:
            params["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        if previous_response_id is not None:
            params["previous_response_id"] = previous_response_id
        if reasoning is not None:
            params["reasoning"] = reasoning
        if text_format is not None:
            params["text_format"] = text_format

        params.update(kwargs)

        routing_config = self._extract_routing_config(model_config)
        if routing_config.timeout:
            params["timeout"] = routing_config.timeout

        response = await litellm.aresponses(**params)
        async for event in response:
            yield event

    # ------------------------------------------------------------------
    # Image Generation (Phase 9)
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        n: int = 1,
        size: str | None = None,
        quality: str | None = None,
        style: str | None = None,
        response_format: str | None = None,
    ) -> ImageGenerationResult:
        """
        Generate images using LiteLLM aimage_generation().

        Supports OpenAI DALL-E, Azure OpenAI, Vertex AI, Bedrock, etc.
        """
        model = model or self.config.get("defaults", {}).get("image_model")
        if not model:
            raise ValueError("Image generation model must be specified")

        full_model = self._get_model_name(model)

        params: dict[str, Any] = {
            "model": full_model,
            "prompt": prompt,
            "n": n,
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint
        if self.api_version:
            params["api_version"] = self.api_version
        if size:
            params["size"] = size
        if quality:
            params["quality"] = quality
        if style:
            params["style"] = style
        if response_format:
            params["response_format"] = response_format

        response = await litellm.aimage_generation(**params)

        # Normalize response data
        images: list[dict[str, Any]] = []
        if hasattr(response, "data") and response.data:
            for img in response.data:
                img_dict: dict[str, Any] = {}
                if hasattr(img, "url") and img.url:
                    img_dict["url"] = img.url
                if hasattr(img, "b64_json") and img.b64_json:
                    img_dict["b64_json"] = img.b64_json
                if hasattr(img, "revised_prompt") and img.revised_prompt:
                    img_dict["revised_prompt"] = img.revised_prompt
                images.append(img_dict)

        return ImageGenerationResult(
            images=images,
            model=full_model,
            raw=response,
        )

    def clear_cache(self) -> None:
        """Clear the in-memory response cache."""
        response_cache.clear()
