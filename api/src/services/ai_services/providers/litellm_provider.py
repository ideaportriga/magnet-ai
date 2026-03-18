"""
LiteLLM Provider implementation with Router for load balancing, failover, and rate limiting.

This provider extends BaseLiteLLMProvider to add:
- Load balancing across multiple model deployments (Router mode)
- Automatic failover when a model/deployment fails
- Rate limiting (RPM/TPM)
- Batch processing with Router support
- Provider-level caching (optional, configurable)

Configuration Modes:

1. Router Mode (with model_list in router_config):
   Uses LiteLLM Router for load balancing across pre-configured deployments.

2. Direct Mode (without model_list):
   Uses litellm.acompletion directly, inherits all BaseLiteLLMProvider features
   including supported-params checking, reasoning model support, etc.

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
from typing import Any, cast

import litellm
from litellm import Router
from litellm.types.utils import EmbeddingResponse as LiteLLMEmbeddingResponse
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.models import EmbeddingResponse, ModelUsage, RoutingConfig
from services.ai_services.providers.base_litellm import BaseLiteLLMProvider

logger = logging.getLogger(__name__)


class LiteLLMProvider(BaseLiteLLMProvider):
    """
    LiteLLM Provider with support for:
    - Router Mode: Load balancing across multiple deployments (requires model_list)
    - Direct Mode: Inherits all BaseLiteLLMProvider features (param checking, reasoning, etc.)
    - Automatic failover with fallback_models
    - Rate limiting (RPM/TPM)
    - In-memory response caching
    - Batch processing
    """

    # No prefix — LiteLLM handles model naming internally
    litellm_provider = ""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize LiteLLM Provider.

        Args:
            config: Provider configuration containing:
                - connection: API key, endpoint, Redis config (optional)
                - defaults: Default model parameters
                - router_config: Router configuration with optional model_list
        """
        super().__init__(config)

        router_config = config.get("router_config", {})

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

        # Additional model defaults for embeddings/rerank
        self.embedding_model = router_config.get("embedding_model")
        self.rerank_model = router_config.get("rerank_model")

        # Default routing config for direct mode
        self._default_routing_raw = router_config.get("default_routing", {})

    def _extract_routing_config(self, model_config: dict | None) -> RoutingConfig:
        """Extract routing_config, falling back to provider-level default_routing."""
        if model_config:
            raw = model_config.get("routing_config")
            if raw:
                return RoutingConfig.from_dict(raw)
        return RoutingConfig.from_dict(self._default_routing_raw)

    async def _execute_completion(
        self,
        params: dict[str, Any],
        routing_config: RoutingConfig,
        model_config: dict | None,
    ) -> ChatCompletion:
        """Execute completion using own Router or direct litellm call.

        Overrides BaseLiteLLMProvider to route through the provider-level
        Router when configured, enabling load balancing across deployments.
        """
        if self.use_router and self.router:
            # Strip provider-specific connection params — Router has its own
            router_params = {
                k: v
                for k, v in params.items()
                if k not in ("api_key", "api_base", "api_version")
            }
            response = await self.router.acompletion(**router_params)
            return cast(ChatCompletion, response)

        # Direct mode — add connection params and call litellm
        if self.api_key and "api_key" not in params:
            params["api_key"] = self.api_key
        if self.endpoint and "api_base" not in params:
            params["api_base"] = self.endpoint
        if self.api_version and "api_version" not in params:
            params["api_version"] = self.api_version

        # Handle fallback models in direct mode
        if routing_config.fallback_models:
            params["fallbacks"] = [{"model": m} for m in routing_config.fallback_models]

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
        """
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
        model_config: dict | None = None,
    ) -> EmbeddingResponse:
        """Get embeddings using LiteLLM, with Router support."""
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

    async def batch_completions(
        self,
        requests: list[dict[str, Any]],
        model_config: dict | None = None,
    ) -> list[ChatCompletion]:
        """Execute multiple completion requests in parallel, with Router support."""
        batch_params = []
        for req in requests:
            model = req.get("model", self.model_default)
            params: dict[str, Any] = {
                "model": self._get_model_name(model) if model else model,
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
            responses = await litellm.abatch_completion(batch_params)

        return [cast(ChatCompletion, r) for r in responses]

    # --- Admin / monitoring methods ---

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
