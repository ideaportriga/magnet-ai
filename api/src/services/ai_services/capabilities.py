"""
Auto-detect model capabilities and pricing from LiteLLM.

Uses litellm.get_model_info() to retrieve model metadata including:
- Supported features (vision, audio, tool calling, JSON mode, etc.)
- Context window sizes (max input/output tokens)
- Pricing information (cost per token)

This eliminates the need to manually configure capabilities for each model.
"""

import logging
from typing import Any

import litellm

from services.ai_services.providers.universal import PROVIDER_TYPE_TO_LITELLM_PREFIX

logger = logging.getLogger(__name__)


def get_litellm_model_name(ai_model: str, provider_type: str) -> str:
    """Build the full litellm model name with provider prefix."""
    prefix = PROVIDER_TYPE_TO_LITELLM_PREFIX.get(provider_type, "")
    if prefix:
        return f"{prefix}/{ai_model}"
    return ai_model


def detect_model_capabilities(
    ai_model: str,
    provider_type: str,
) -> dict[str, Any]:
    """
    Auto-detect model capabilities from LiteLLM's model info database.

    Args:
        ai_model: The model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")
        provider_type: Provider type (e.g., "openai", "anthropic")

    Returns:
        Dict with detected capabilities. Empty dict if model not found in LiteLLM.

    Example return:
        {
            "json_mode": True,
            "json_schema": True,
            "tool_calling": True,
            "reasoning": False,
            "supports_vision": True,
            "supports_audio_input": False,
            "supports_audio_output": False,
            "supports_pdf_input": True,
            "supports_prompt_caching": True,
            "supports_streaming": True,
            "max_input_tokens": 128000,
            "max_output_tokens": 16384,
        }
    """
    full_model = get_litellm_model_name(ai_model, provider_type)

    try:
        info = litellm.get_model_info(full_model)
    except Exception:
        # Model not found in LiteLLM's database — try without prefix
        try:
            info = litellm.get_model_info(ai_model)
        except Exception:
            logger.debug(
                "Model '%s' (prefix: '%s') not found in LiteLLM model info",
                ai_model,
                provider_type,
            )
            return {}

    capabilities: dict[str, Any] = {}

    # Feature support flags
    capabilities["json_mode"] = info.get("supports_response_schema", False)
    capabilities["json_schema"] = info.get("supports_response_schema", False)
    capabilities["tool_calling"] = info.get("supports_function_calling", False)
    capabilities["reasoning"] = info.get("supports_reasoning", False)
    capabilities["supports_vision"] = info.get("supports_vision", False)
    capabilities["supports_audio_input"] = info.get("supports_audio_input", False)
    capabilities["supports_audio_output"] = info.get("supports_audio_output", False)
    capabilities["supports_pdf_input"] = info.get("supports_pdf_input", False)
    capabilities["supports_prompt_caching"] = info.get("supports_prompt_caching", False)
    capabilities["supports_streaming"] = True  # Most models support streaming
    capabilities["supports_web_search"] = info.get("supports_web_search", False)

    # Context window sizes
    max_input = info.get("max_input_tokens")
    if max_input is not None:
        capabilities["max_input_tokens"] = max_input

    max_output = info.get("max_output_tokens")
    if max_output is not None:
        capabilities["max_output_tokens"] = max_output

    return capabilities


def detect_model_pricing(
    ai_model: str,
    provider_type: str,
) -> dict[str, Any]:
    """
    Auto-detect model pricing from LiteLLM's model info database.

    Args:
        ai_model: The model identifier
        provider_type: Provider type

    Returns:
        Dict with pricing info. Empty dict if not found.

    Example return:
        {
            "price_input": 0.0000025,   # per token
            "price_output": 0.00001,    # per token
            "price_cached": 0.00000125, # per cached input token (if supported)
        }
    """
    full_model = get_litellm_model_name(ai_model, provider_type)

    try:
        info = litellm.get_model_info(full_model)
    except Exception:
        try:
            info = litellm.get_model_info(ai_model)
        except Exception:
            return {}

    pricing: dict[str, Any] = {}

    input_cost = info.get("input_cost_per_token")
    if input_cost is not None:
        pricing["price_input"] = input_cost

    output_cost = info.get("output_cost_per_token")
    if output_cost is not None:
        pricing["price_output"] = output_cost

    cache_cost = info.get("cache_read_input_token_cost")
    if cache_cost is not None:
        pricing["price_cached"] = cache_cost

    return pricing


def get_supported_params(
    ai_model: str,
    provider_type: str,
) -> list[str]:
    """
    Get list of OpenAI-compatible parameters supported by the model.

    Useful for validating request parameters before sending.

    Args:
        ai_model: The model identifier
        provider_type: Provider type

    Returns:
        List of supported parameter names, or empty list if unknown.
    """
    full_model = get_litellm_model_name(ai_model, provider_type)

    try:
        params = litellm.get_supported_openai_params(full_model)
        return list(params) if params else []
    except Exception:
        return []
