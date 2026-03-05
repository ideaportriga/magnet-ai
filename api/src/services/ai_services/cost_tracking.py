"""
Cost tracking using LiteLLM's built-in pricing database.

Provides a hybrid approach:
- Custom pricing from DB (AIModel.price_input/price_output) takes priority
- Falls back to LiteLLM's built-in pricing for 1000+ models
- LiteLLM pricing is updated with each litellm release

Usage:
    cost = get_response_cost(response, model_system_name)
    # or
    cost = get_litellm_cost(response)
"""

import logging
from typing import Any

import litellm

logger = logging.getLogger(__name__)


def get_litellm_cost(response: Any) -> float:
    """
    Get cost from LiteLLM's built-in cost calculation.

    LiteLLM automatically calculates cost based on its internal
    pricing database (model_prices_and_context_window.json).

    Args:
        response: LiteLLM response object (ChatCompletion, EmbeddingResponse, etc.)

    Returns:
        Cost in USD, or 0.0 if unable to calculate.
    """
    # First try _hidden_params (set by litellm automatically)
    if hasattr(response, "_hidden_params"):
        cost = response._hidden_params.get("response_cost")
        if cost is not None:
            return float(cost)

    # Fallback: explicit calculation
    try:
        return float(litellm.completion_cost(completion_response=response))
    except Exception:
        logger.debug("Unable to calculate litellm cost", exc_info=True)
        return 0.0


def get_response_cost(
    response: Any,
    model_config: dict[str, Any] | None = None,
) -> float:
    """
    Get cost using custom pricing from DB, falling back to LiteLLM.

    Priority:
    1. Custom pricing from model_config (price_input + price_output)
    2. LiteLLM's built-in pricing

    Args:
        response: LiteLLM response object
        model_config: AIModel configuration dict (optional)

    Returns:
        Cost in USD
    """
    # Try custom pricing from DB first
    if model_config:
        price_input = model_config.get("price_input")
        price_output = model_config.get("price_output")

        if price_input is not None and price_output is not None:
            try:
                usage = getattr(response, "usage", None)
                if usage:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                    input_cost = float(price_input) * prompt_tokens
                    output_cost = float(price_output) * completion_tokens
                    return input_cost + output_cost
            except Exception:
                logger.debug("Error calculating custom cost", exc_info=True)

    # Fallback to LiteLLM
    return get_litellm_cost(response)


def get_model_pricing_from_litellm(
    ai_model: str,
    provider_type: str = "",
) -> dict[str, float | None]:
    """
    Look up model pricing from LiteLLM's pricing database.

    Useful for auto-populating pricing fields when creating a model.

    Args:
        ai_model: Model identifier (e.g., "gpt-4o")
        provider_type: Provider type for prefix (e.g., "openai")

    Returns:
        Dict with price_input, price_output, price_cached (per token, in USD)
    """
    from services.ai_services.providers.universal import PROVIDER_TYPE_TO_LITELLM_PREFIX

    prefix = PROVIDER_TYPE_TO_LITELLM_PREFIX.get(provider_type, "")
    full_model = f"{prefix}/{ai_model}" if prefix else ai_model

    try:
        info = litellm.get_model_info(full_model)
    except Exception:
        try:
            info = litellm.get_model_info(ai_model)
        except Exception:
            return {
                "price_input": None,
                "price_output": None,
                "price_cached": None,
            }

    return {
        "price_input": info.get("input_cost_per_token"),
        "price_output": info.get("output_cost_per_token"),
        "price_cached": info.get("cache_read_input_token_cost"),
    }
