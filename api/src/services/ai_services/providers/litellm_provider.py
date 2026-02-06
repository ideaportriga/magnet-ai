"""
LiteLLM Provider implementation with Router for load balancing, failover, and rate limiting.

This provider wraps LiteLLM's Router to provide:
- Load balancing across multiple model deployments
- Automatic failover when a model/deployment fails
- Rate limiting (RPM/TPM)
- Batch processing support
- Caching (optional, configurable)
- Support for routing_config from AIModel

Configuration Modes:

1. Router Mode (with model_list in router_config):
   Uses LiteLLM Router for load balancing across pre-configured deployments.

2. Direct Mode (without model_list):
   Uses litellm.acompletion directly, supports routing_config from AIModel.

Configuration Example (Router Mode):
{
    "connection": {
        "api_key": "...",
        "endpoint": "https://api.openai.com/v1",
        "redis_host": "localhost",  # Optional: for distributed rate limiting
        "redis_port": 6379,
        "cache_enabled": false
    },
    "defaults": {
        "model": "gpt-4o",
        "temperature": 0.7,
        "top_p": 1.0
    },
    "router_config": {
        "routing_strategy": "simple-shuffle",
        "num_retries": 3,
        "model_list": [...]
    }
}

Configuration Example (Direct Mode with AIModel routing_config):
{
    "connection": {
        "api_key": "...",
        "endpoint": "https://api.openai.com/v1"
    },
    "defaults": {
        "model": "gpt-4o",
        "temperature": 0.7
    }
}

AIModel routing_config example:
{
    "rpm": 1000,
    "tpm": 100000,
    "fallback_models": ["gpt-4o-mini", "claude-3-sonnet"],
    "cache_enabled": true,
    "cache_ttl": 3600,
    "num_retries": 3,
    "timeout": 120
}
"""

import logging
from decimal import Decimal
from hashlib import md5
from time import time
from typing import Any, cast

import litellm
from litellm import Router
from litellm.types.utils import EmbeddingResponse as LiteLLMEmbeddingResponse
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from models import DocumentSearchResult
from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage, RerankResponse

logger = logging.getLogger(__name__)

# Suppress verbose litellm logging
litellm.suppress_debug_info = True


class InMemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size

    def make_key(self, **kwargs) -> str:
        """Create cache key from request parameters."""
        # Filter out non-hashable items and create stable key
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
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        expires_at = time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expires_at)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


# Global cache instance for in-memory caching
_response_cache = InMemoryCache()


class LiteLLMProvider(AIProviderInterface):
    """
    LiteLLM Provider with support for:
    - Router Mode: Load balancing across multiple deployments (requires model_list)
    - Direct Mode: Direct calls with routing_config from AIModel
    - Automatic failover with fallback_models
    - Rate limiting (RPM/TPM)
    - In-memory response caching
    - Batch processing
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize LiteLLM Provider.

        Args:
            config: Provider configuration containing:
                - connection: API key, endpoint, Redis config (optional)
                - defaults: Default model parameters
                - router_config: Router configuration with optional model_list
        """
        self.config = config
        self.connection = config.get("connection", {})
        defaults = config.get("defaults", {})
        router_config = config.get("router_config", {})

        # Store connection params for direct mode
        self.api_key = self.connection.get("api_key")
        self.endpoint = self.connection.get("endpoint")
        self.api_version = self.connection.get("api_version")

        # Store defaults
        self.model_default = defaults.get("model")
        self.temperature_default = defaults.get("temperature")
        self.top_p_default = defaults.get("top_p")

        # Router mode vs Direct mode
        model_list = router_config.get("model_list", [])
        self.use_router = bool(model_list)
        self.router: Router | None = None

        if self.use_router:
            # Initialize Router for load balancing
            router_kwargs: dict[str, Any] = {
                "model_list": model_list,
                "routing_strategy": router_config.get(
                    "routing_strategy", "simple-shuffle"
                ),
                "num_retries": router_config.get("num_retries", 3),
                "retry_after": router_config.get("retry_after", 5),
                "timeout": router_config.get("timeout", 120),
                "allowed_fails": router_config.get("allowed_fails", 3),
                "cooldown_time": router_config.get("cooldown_time", 60),
            }

            # Optional Redis for distributed rate limiting
            redis_host = self.connection.get("redis_host")
            if redis_host:
                router_kwargs["redis_host"] = redis_host
                router_kwargs["redis_port"] = self.connection.get("redis_port", 6379)
                router_kwargs["redis_password"] = self.connection.get("redis_password")

            # Optional caching via Router
            if self.connection.get("cache_enabled"):
                router_kwargs["cache_responses"] = True
                cache_config = self.connection.get("cache_config", {})
                if cache_config:
                    router_kwargs["cache_kwargs"] = cache_config

            self.router = Router(**router_kwargs)

        # Store additional model configs
        self.embedding_model = router_config.get("embedding_model")
        self.rerank_model = router_config.get("rerank_model")

        # Default routing config for direct mode
        self.default_routing_config = router_config.get("default_routing", {})

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
        Create chat completion using LiteLLM.

        Supports both Router mode and Direct mode based on provider configuration.
        When using Direct mode, routing_config from model_config is applied.
        """
        model = model or self.model_default
        if not model:
            raise ValueError("Model must be specified either in request or defaults")

        temperature = (
            temperature if temperature is not None else self.temperature_default
        )
        top_p = top_p if top_p is not None else self.top_p_default

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        # Add optional parameters
        if temperature is not None:
            if model_config and model_config.get("reasoning"):
                params["reasoning_effort"] = model_config.get("reasoning_effort", "low")
            else:
                params["temperature"] = temperature

        if top_p is not None:
            params["top_p"] = top_p

        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        if response_format is not None:
            params["response_format"] = self._transform_response_format(response_format)

        if tools is not None:
            params["tools"] = tools

        if tool_choice is not None:
            params["tool_choice"] = tool_choice

        if parallel_tool_calls is not None and tools:
            params["parallel_tool_calls"] = parallel_tool_calls

        # Extract routing_config from model_config if provided
        routing_config = (model_config or {}).get(
            "routing_config"
        ) or self.default_routing_config

        # Check cache if enabled
        cache_enabled = routing_config.get("cache_enabled", False)
        cache_key = None
        if cache_enabled and not tools:  # Don't cache tool calls
            cache_key = _response_cache.make_key(model=model, messages=str(messages))
            cached = _response_cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for model {model}")
                return cached

        # Execute request
        if self.use_router and self.router:
            response = await self._call_with_router(params, routing_config)
        else:
            response = await self._call_direct(params, routing_config)

        # Cache response if enabled
        if cache_key:
            cache_ttl = routing_config.get("cache_ttl", 3600)
            _response_cache.set(cache_key, response, ttl=cache_ttl)

        return cast(ChatCompletion, response)

    async def _call_with_router(
        self, params: dict[str, Any], routing_config: dict[str, Any]
    ) -> ChatCompletion:
        """Execute request using LiteLLM Router."""
        response = await self.router.acompletion(**params)
        return cast(ChatCompletion, response)

    async def _call_direct(
        self, params: dict[str, Any], routing_config: dict[str, Any]
    ) -> ChatCompletion:
        """
        Execute request directly using litellm.acompletion with routing_config.

        Supports:
        - fallback_models for automatic failover
        - num_retries for retry logic
        - timeout configuration
        """
        # Add connection params
        if self.api_key:
            params["api_key"] = self.api_key
        if self.endpoint:
            params["api_base"] = self.endpoint
        if self.api_version:
            params["api_version"] = self.api_version

        # Add extra params from routing_config
        extra_params = routing_config.get("litellm_params", {})
        params.update(extra_params)

        # Set timeout
        timeout = routing_config.get("timeout", 120)
        params["timeout"] = timeout

        # Set retries
        num_retries = routing_config.get("num_retries", 3)
        params["num_retries"] = num_retries

        # Handle fallback models
        fallback_models = routing_config.get("fallback_models", [])
        if fallback_models:
            params["fallbacks"] = [{"model": m} for m in fallback_models]

        response = await litellm.acompletion(**params)
        return cast(ChatCompletion, response)

    async def create_chat_completion_with_routing(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str,
        routing_config: dict[str, Any],
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
    ) -> ChatCompletion:
        """
        Create chat completion with explicit routing_config.

        This method allows passing routing_config directly for more control
        over rate limiting, fallbacks, and caching per-request.

        Args:
            messages: Chat messages
            model: Model name
            routing_config: Routing configuration from AIModel.routing_config
            ... other standard completion params
        """
        # Merge routing_config into model_config
        merged_config = {**(model_config or {}), "routing_config": routing_config}

        return await self.create_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            model_config=merged_config,
        )

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        """Get embeddings using LiteLLM."""
        model = llm or self.embedding_model
        if model is None:
            raise ValueError(
                "Model name must be provided or embedding_model must be configured"
            )

        if self.use_router and self.router:
            response: LiteLLMEmbeddingResponse = await self.router.aembedding(
                model=model,
                input=[text],
            )
        else:
            # Direct call
            kwargs: dict[str, Any] = {"model": model, "input": [text]}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.endpoint:
                kwargs["api_base"] = self.endpoint

            response = await litellm.aembedding(**kwargs)

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
        model = llm or self.rerank_model
        if model is None:
            raise ValueError(
                "Model name must be provided or rerank_model must be configured"
            )

        doc_texts = [doc.content or "" for doc in documents]

        response = await litellm.arerank(
            model=model,
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
    ) -> list[ChatCompletion]:
        """Execute multiple completion requests in parallel."""
        batch_params = []
        for req in requests:
            params = {
                "model": req.get("model", self.model_default),
                "messages": req["messages"],
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

        if self.use_router and self.router:
            responses = await self.router.abatch_completion(batch_params)
        else:
            # Use litellm batch for direct mode
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

    async def get_available_models(self) -> list[str]:
        """Get list of available model names."""
        if self.use_router and self.router:
            return list(set(m["model_name"] for m in self.router.model_list))
        return [self.model_default] if self.model_default else []

    async def get_model_info(self, model: str) -> dict[str, Any]:
        """Get information about a specific model."""
        if not self.use_router or not self.router:
            return {"model_name": model, "mode": "direct"}

        deployments = [m for m in self.router.model_list if m["model_name"] == model]
        return {
            "model_name": model,
            "mode": "router",
            "num_deployments": len(deployments),
            "deployments": [
                {
                    "model": d["litellm_params"].get("model"),
                    "rpm": d["litellm_params"].get("rpm"),
                    "tpm": d["litellm_params"].get("tpm"),
                }
                for d in deployments
            ],
        }

    def get_router_stats(self) -> dict[str, Any]:
        """Get current router statistics for monitoring."""
        if not self.use_router or not self.router:
            return {"mode": "direct", "router_enabled": False}

        return {
            "mode": "router",
            "router_enabled": True,
            "healthy_deployments": self.router.get_healthy_deployments(),
            "model_list": [m["model_name"] for m in self.router.model_list],
            "routing_strategy": self.router.routing_strategy,
        }

    def clear_cache(self) -> None:
        """Clear the in-memory response cache."""
        _response_cache.clear()
