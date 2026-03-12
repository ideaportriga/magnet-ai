"""
AI services utility functions.

Note: Dead code was removed in the LiteLLM integration cleanup (Phase 0):
- get_provider_by_model() — unused, duplicated logic in factory.get_ai_provider()
- build_litellm_model_entry() — duplicated logic in router._build_router_config()
- get_model_config_with_routing() — unused externally
"""

from typing import Any

from services.ai_services.providers.universal import PROVIDER_TYPE_TO_LITELLM_PREFIX

# Default base URLs for cloud providers (no custom endpoint configured)
_DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com",
    "anthropic": "https://api.anthropic.com",
    "groq": "https://api.groq.com/openai",
    "gemini": "https://generativelanguage.googleapis.com",
    "mistral": "https://api.mistral.ai",
    "deepseek": "https://api.deepseek.com",
    "cohere": "https://api.cohere.ai",
    "perplexity": "https://api.perplexity.ai",
    "xai": "https://api.x.ai",
    "cerebras": "https://api.cerebras.ai",
    "sambanova": "https://api.sambanova.ai",
    "together_ai": "https://api.together.xyz/v1",
    "fireworks_ai": "https://api.fireworks.ai/inference",
    "openrouter": "https://openrouter.ai/api",
    "ai21": "https://api.ai21.com",
    "friendliai": "https://inference.friendli.ai",
}


def get_litellm_debug_info(
    provider_data: dict[str, Any],
    model_name: str,
    model_system_name: str,
    model_routing_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compute LiteLLM routing diagnostic information for a model.

    Returns a dict suitable for spreading into ProviderTestResult / ModelTestResult:
        {
            "litellm_model_string": str | None,
            "effective_endpoint":   str | None,
            "via_router":           bool,
            "computed_url":         str | None,
        }

    Args:
        provider_data: dict with keys: type, endpoint, connection_config
        model_name: model.ai_model value (e.g. "gpt-4o", "my-azure-deployment")
        model_system_name: model.system_name used as the Router deployment name
        model_routing_config: optional routing_config dict from the AIModel record
                              (may contain litellm_params.api_base override)
    """
    from services.ai_services.router import is_model_in_router

    provider_type: str = provider_data.get("type") or ""
    provider_endpoint: str | None = provider_data.get("endpoint")
    connection_config: dict = provider_data.get("connection_config") or {}

    # 1. LiteLLM model prefix
    litellm_prefix = PROVIDER_TYPE_TO_LITELLM_PREFIX.get(provider_type)
    if litellm_prefix is None:
        # Unknown type — fall back to openai/ if endpoint exists (mirrors router.py:133)
        litellm_prefix = "openai" if provider_endpoint else None

    if litellm_prefix:
        litellm_model_string = f"{litellm_prefix}/{model_name}"
    else:
        litellm_model_string = model_name if model_name else None

    # 2. Effective endpoint — model-level override wins over provider-level
    model_level_endpoint: str | None = None
    if model_routing_config:
        litellm_params = model_routing_config.get("litellm_params") or {}
        model_level_endpoint = litellm_params.get("api_base") or litellm_params.get(
            "base_url"
        )

    effective_endpoint = model_level_endpoint or provider_endpoint

    # 3. Whether the model routes through the global LiteLLM Router
    via_router = is_model_in_router(model_system_name)

    # 4. Computed URL — best-effort approximation of what LiteLLM will call
    computed_url = _build_computed_url(
        provider_type=provider_type,
        model_name=model_name,
        endpoint=effective_endpoint,
        connection_config=connection_config,
    )

    return {
        "litellm_model_string": litellm_model_string,
        "effective_endpoint": effective_endpoint,
        "via_router": via_router,
        "computed_url": computed_url,
    }


def _build_computed_url(
    provider_type: str,
    model_name: str,
    endpoint: str | None,
    connection_config: dict[str, Any],
) -> str | None:
    """Build the approximate full URL that LiteLLM will send requests to."""

    if provider_type == "azure_open_ai":
        base = (endpoint or "").rstrip("/")
        if not base:
            return None
        api_version = connection_config.get("api_version", "2024-02-01")
        return (
            f"{base}/openai/deployments/{model_name}"
            f"/chat/completions?api-version={api_version}"
        )

    if provider_type == "azure_ai":
        base = (endpoint or "").rstrip("/")
        if not base:
            return None
        api_version = connection_config.get("api_version", "2024-05-01-preview")
        return f"{base}/chat/completions?api-version={api_version}"

    # For embedding / rerank models the path differs, but we show the base URL
    base = endpoint or _DEFAULT_BASE_URLS.get(provider_type)
    if not base:
        return None

    return f"{base.rstrip('/')}/v1/chat/completions"
