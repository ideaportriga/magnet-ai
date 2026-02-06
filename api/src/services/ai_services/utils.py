import logging
from typing import Any

from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider


async def get_provider_by_model(system_name_for_model: str):
    try:
        provider_system_name = None
        if system_name_for_model:
            model_config = await get_model_by_system_name(system_name_for_model)
            if model_config:
                provider_system_name_from_config = model_config.get(
                    "provider_system_name"
                )
                if isinstance(provider_system_name_from_config, str):
                    provider_system_name = provider_system_name_from_config

        if not provider_system_name:
            raise ValueError(
                f"Model '{system_name_for_model}' does not have a provider_system_name configured"
            )

        provider = await get_ai_provider(provider_system_name)
        return provider

    except Exception as e:
        logging.exception(
            f"Error retrieving provider for model {system_name_for_model}: {e}",
        )
        raise


async def get_model_config_with_routing(system_name_for_model: str) -> dict[str, Any]:
    """
    Get model configuration including routing_config for LiteLLM.

    Returns dict with:
    - model_config: Full model configuration
    - routing_config: Extracted routing config (rpm, tpm, fallback_models, etc.)
    - ai_model: The actual model name to call
    - provider_system_name: Provider to use
    """
    model_config = await get_model_by_system_name(system_name_for_model)

    if not model_config:
        raise ValueError(f"Model '{system_name_for_model}' not found")

    routing_config = model_config.get("routing_config") or {}

    return {
        "model_config": model_config,
        "routing_config": routing_config,
        "ai_model": model_config.get("ai_model"),
        "provider_system_name": model_config.get("provider_system_name"),
        "system_name": system_name_for_model,
    }


def build_litellm_model_entry(
    model_config: dict[str, Any],
    provider_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Build a LiteLLM model_list entry from AIModel and Provider configurations.

    Args:
        model_config: AIModel configuration with routing_config
        provider_config: Provider configuration with connection details

    Returns:
        LiteLLM model_list entry for Router
    """
    routing_config = model_config.get("routing_config") or {}
    connection = provider_config.get("connection", {})

    # Build litellm_params from provider connection and model config
    litellm_params: dict[str, Any] = {
        "model": model_config.get("ai_model"),
    }

    # Add connection params from provider
    if connection.get("api_key"):
        litellm_params["api_key"] = connection["api_key"]
    if connection.get("endpoint"):
        litellm_params["api_base"] = connection["endpoint"]
    if connection.get("api_version"):
        litellm_params["api_version"] = connection["api_version"]

    # Add rate limits from routing_config
    if routing_config.get("rpm"):
        litellm_params["rpm"] = routing_config["rpm"]
    if routing_config.get("tpm"):
        litellm_params["tpm"] = routing_config["tpm"]

    # Merge any additional litellm_params from routing_config
    extra_params = routing_config.get("litellm_params") or {}
    litellm_params.update(extra_params)

    return {
        "model_name": model_config.get("system_name", model_config.get("ai_model")),
        "litellm_params": litellm_params,
    }
