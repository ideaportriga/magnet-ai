"""
Centralized AI Router service using LiteLLM Router.

Provides cross-provider fallback, load balancing, rate limiting,
and caching for all AI models.
"""

from __future__ import annotations

import logging
from typing import Any

from litellm import Router
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from core.config.app import alchemy
from core.domain.ai_models.service import AIModelsService
from core.domain.providers.service import ProvidersService
from utils.secrets import replace_placeholders_in_dict

logger = logging.getLogger(__name__)

# Global router instance
_router: Router | None = None
_router_initialized: bool = False

# Provider type to LiteLLM provider prefix mapping
PROVIDER_TYPE_TO_LITELLM = {
    "openai": "openai",
    "azure_open_ai": "azure",
    "azure_ai": "azure_ai",
    "groq": "groq",
    "datakom": "",  # Local/custom endpoints
    "litellm": "",  # Already LiteLLM format
}


async def _build_model_list() -> list[dict[str, Any]]:
    """
    Build LiteLLM Router model_list from database models and providers.

    Returns:
        List of model configurations for LiteLLM Router
    """
    model_list = []

    async with alchemy.get_session() as session:
        # Load all models
        models_service = AIModelsService(session=session)
        providers_service = ProvidersService(session=session)

        all_models = await models_service.list()
        providers_cache: dict[str, dict] = {}

        for model in all_models:
            if not model.provider_system_name:
                logger.warning(
                    f"Model {model.system_name} has no provider_system_name, skipping"
                )
                continue

            # Get provider config (cached)
            if model.provider_system_name not in providers_cache:
                provider = await providers_service.get_one_or_none(
                    system_name=model.provider_system_name
                )
                if not provider:
                    logger.warning(
                        f"Provider {model.provider_system_name} not found for model {model.system_name}"
                    )
                    continue

                # Build provider config
                connection_config = provider.connection_config or {}
                secrets = provider.secrets_encrypted or {}
                resolved_connection = replace_placeholders_in_dict(
                    connection_config, secrets
                )
                providers_cache[model.provider_system_name] = {
                    "type": provider.type,
                    "endpoint": provider.endpoint,
                    "connection": {**secrets, **resolved_connection},
                    "metadata_info": provider.metadata_info or {},
                }

            provider_config = providers_cache[model.provider_system_name]
            provider_type = provider_config["type"]

            # Skip unsupported provider types (OCI uses native SDK)
            if provider_type in ("oci", "oci_llama"):
                logger.debug(
                    f"Skipping OCI model {model.system_name} - uses native SDK"
                )
                continue

            # Build litellm_params
            litellm_provider = PROVIDER_TYPE_TO_LITELLM.get(provider_type, "")
            model_name = model.ai_model

            # Construct full model name with provider prefix
            if litellm_provider:
                full_model_name = f"{litellm_provider}/{model_name}"
            else:
                full_model_name = model_name

            litellm_params: dict[str, Any] = {
                "model": full_model_name,
            }

            # Add API key
            connection = provider_config["connection"]
            if "api_key" in connection:
                litellm_params["api_key"] = connection["api_key"]

            # Add endpoint/base URL
            endpoint = provider_config.get("endpoint")
            if endpoint:
                if provider_type == "azure_open_ai":
                    litellm_params["api_base"] = endpoint
                else:
                    litellm_params["base_url"] = endpoint

            # Azure-specific params
            if provider_type == "azure_open_ai":
                litellm_params["api_version"] = connection.get(
                    "api_version", "2024-02-01"
                )

            # Azure AI specific
            if provider_type == "azure_ai":
                litellm_params["api_version"] = connection.get(
                    "api_version", "2024-05-01-preview"
                )

            # Get routing config from model
            routing_config = model.routing_config or {}

            # Build model entry for Router
            model_entry: dict[str, Any] = {
                "model_name": model.system_name,  # Use system_name as deployment name
                "litellm_params": litellm_params,
            }

            # Add rate limiting
            if routing_config.get("rpm"):
                model_entry["rpm"] = routing_config["rpm"]
            if routing_config.get("tpm"):
                model_entry["tpm"] = routing_config["tpm"]

            # Add priority and weight for load balancing
            if routing_config.get("priority"):
                model_entry["priority"] = routing_config["priority"]
            if routing_config.get("weight"):
                model_entry["weight"] = routing_config["weight"]

            # Add extra litellm_params from routing_config
            extra_params = routing_config.get("litellm_params", {})
            if extra_params:
                model_entry["litellm_params"].update(extra_params)

            model_list.append(model_entry)

            logger.debug(
                f"Added model {model.system_name} to router: {full_model_name}"
            )

    return model_list


async def _build_fallback_map() -> dict[str, list[str]]:
    """
    Build fallback map from model routing_config.

    Returns:
        Dict mapping model system_name to list of fallback model system_names
    """
    fallback_map = {}

    async with alchemy.get_session() as session:
        models_service = AIModelsService(session=session)
        all_models = await models_service.list()

        for model in all_models:
            routing_config = model.routing_config or {}
            fallback_models = routing_config.get("fallback_models", [])
            if fallback_models:
                fallback_map[model.system_name] = fallback_models

    return fallback_map


async def get_router() -> Router:
    """
    Get or create the global LiteLLM Router.

    Returns:
        Configured LiteLLM Router instance
    """
    global _router, _router_initialized

    if _router is not None and _router_initialized:
        return _router

    model_list = await _build_model_list()
    fallback_map = await _build_fallback_map()

    if not model_list:
        logger.warning("No models configured for LiteLLM Router")
        # Create empty router
        _router = Router(model_list=[])
        _router_initialized = True
        return _router

    # Configure router settings
    # NOTE: num_retries / timeout here are Router-level defaults.
    # Per-model values from routing_config are passed as kwargs to
    # router.acompletion() and override these defaults.
    router_settings = {
        "model_list": model_list,
        "routing_strategy": "simple-shuffle",  # Default strategy
        "num_retries": 0,  # Default: no retries, fallback immediately
        "timeout": 30,
        "retry_after": 0,  # No artificial delay between retries
        "enable_pre_call_checks": True,
    }

    # Add fallbacks if configured
    # LiteLLM expects fallbacks as a list of single-key dicts:
    # [{"model_a": ["fallback_1"]}, {"model_b": ["fallback_2"]}]
    if fallback_map:
        router_settings["fallbacks"] = [
            {model_name: fallback_list}
            for model_name, fallback_list in fallback_map.items()
        ]

    # Create router
    _router = Router(**router_settings)
    _router_initialized = True

    logger.info(f"LiteLLM Router initialized with {len(model_list)} models")

    return _router


async def refresh_router() -> None:
    """
    Refresh the router by reloading all models from database.

    Call this after models or providers are updated.
    """
    global _router, _router_initialized

    _router = None
    _router_initialized = False

    await get_router()
    logger.info("LiteLLM Router refreshed")


async def router_completion(
    model: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
    **kwargs,
) -> ChatCompletion:
    """
    Call chat completion through the centralized router.

    Args:
        model: Model system_name to use
        messages: Chat messages
        temperature: Sampling temperature
        top_p: Top-p sampling
        max_tokens: Maximum tokens to generate
        response_format: Response format specification
        tools: Tool definitions
        tool_choice: Tool choice setting
        **kwargs: Additional LiteLLM parameters

    Returns:
        ChatCompletion response
    """
    router = await get_router()

    # Build request parameters
    params: dict[str, Any] = {
        "model": model,  # This is the model_name (system_name) in router
        "messages": messages,
    }

    if temperature is not None:
        params["temperature"] = temperature
    if top_p is not None:
        params["top_p"] = top_p
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    if response_format is not None:
        params["response_format"] = response_format
    if tools is not None:
        params["tools"] = tools
    if tool_choice is not None:
        params["tool_choice"] = tool_choice

    params.update(kwargs)

    # Call through router
    response = await router.acompletion(**params)

    return response


async def router_embedding(
    model: str,
    input: str | list[str],
    **kwargs,
) -> Any:
    """
    Call embeddings through the centralized router.

    Args:
        model: Model system_name to use
        input: Text or list of texts to embed
        **kwargs: Additional LiteLLM parameters

    Returns:
        Embedding response
    """
    router = await get_router()

    response = await router.aembedding(
        model=model,
        input=input,
        **kwargs,
    )

    return response


def is_model_in_router(model_system_name: str) -> bool:
    """
    Check if a model is available in the router.

    Args:
        model_system_name: Model system_name to check

    Returns:
        True if model is in router, False otherwise
    """
    global _router

    if _router is None:
        return False

    for model in _router.model_list:
        if model.get("model_name") == model_system_name:
            return True

    return False


def get_model_system_name_by_deployment_id(model_id: str) -> str | None:
    """
    Look up the model system_name by its LiteLLM deployment model_id.

    When the Router processes a request (including fallbacks), the response
    contains _hidden_params["model_id"] identifying which deployment handled it.
    This function maps that back to our system_name.

    Args:
        model_id: The deployment model_id from _hidden_params

    Returns:
        The model system_name, or None if not found
    """
    global _router

    if _router is None or not model_id:
        return None

    for model_entry in _router.model_list:
        model_info = model_entry.get("model_info", {})
        if model_info and model_info.get("id") == model_id:
            return model_entry.get("model_name")

    return None
