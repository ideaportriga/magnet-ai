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
from decimal import Decimal
from hashlib import md5
from time import time
from typing import Any, cast

import litellm
from litellm.caching import Cache
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from models import DocumentSearchResult
from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage, RerankResponse

logger = logging.getLogger(__name__)

# Suppress verbose litellm logging
litellm.suppress_debug_info = True

# Configure LiteLLM in-memory cache globally
litellm.cache = Cache(type="local")  # In-memory cache
litellm.enable_cache = (
    False  # Disabled by default, enabled per-request via routing_config
)


class InMemoryCache:
    """Simple in-memory cache with TTL support for response caching.

    Note: This is kept for backward compatibility with OCI providers
    that don't use LiteLLM. For LiteLLM providers, use litellm.cache instead.
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size

    def make_key(self, **kwargs) -> str:
        """Create cache key from request parameters."""
        hashable = {k: str(v) for k, v in sorted(kwargs.items())}
        key_str = str(hashable)
        return md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if time() < expires_at:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        expires_at = time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expires_at)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


# Global cache instance for OCI providers (non-LiteLLM)
_response_cache = InMemoryCache()


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

    def _extract_routing_config(self, model_config: dict | None) -> dict[str, Any]:
        """Extract routing_config from model_config or return empty dict."""
        if not model_config:
            return {}
        return model_config.get("routing_config") or {}

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

        full_model = self._get_model_name(model)
        temperature = (
            temperature if temperature is not None else self.temperature_default
        )
        top_p = top_p if top_p is not None else self.top_p_default
        max_tokens = max_tokens or self.max_tokens_default

        # Extract routing configuration
        routing_config = self._extract_routing_config(model_config)

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
                    "reasoning_effort", "low"
                )
            elif "temperature" in supported_params:
                params["temperature"] = temperature

        if top_p is not None and "top_p" in supported_params:
            params["top_p"] = top_p

        if max_tokens is not None:
            # Prefer max_completion_tokens if supported, otherwise use max_tokens
            if (
                "max_completion_tokens" in supported_params
                and "max_tokens" not in supported_params
            ):
                params["max_completion_tokens"] = max_tokens
            elif "max_tokens" in supported_params:
                params["max_tokens"] = max_tokens
            else:
                # Both supported - use max_completion_tokens for newer models
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
        if routing_config.get("timeout"):
            params["timeout"] = routing_config["timeout"]

        if routing_config.get("num_retries"):
            params["num_retries"] = routing_config["num_retries"]

        # Handle fallback models — use Router if fallbacks are configured,
        # because fallback_models contains system_names that only the Router
        # can resolve to actual model configs with proper API keys/endpoints.
        fallback_models = routing_config.get("fallback_models") or []
        use_router = bool(fallback_models)

        # Extra LiteLLM params from routing_config
        extra_params = routing_config.get("litellm_params") or {}
        if extra_params:
            params.update(extra_params)

        # Enable LiteLLM built-in cache if configured (not for tool calls)
        cache_enabled = routing_config.get("cache_enabled", False)
        if cache_enabled and not tools:
            params["caching"] = True
            cache_ttl = routing_config.get("cache_ttl", 3600)
            params["cache"] = {"ttl": cache_ttl}

        # Execute request
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
        """Transform response format for LiteLLM compatibility."""
        if response_format is None:
            return None

        if response_format.get("type") == "json_schema":
            return response_format

        if response_format.get("type") == "json_object":
            return {"type": "json_object"}

        return response_format

    def clear_cache(self) -> None:
        """Clear the in-memory response cache."""
        _response_cache.clear()
