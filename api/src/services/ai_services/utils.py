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
    model_type: str | None = None,
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
        model_type: optional model type ("prompts", "embeddings", "re-ranking")
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

    # 2. Effective endpoint — api_path is appended to provider endpoint (path-only, no host override)
    api_path: str | None = None
    if model_routing_config:
        api_path = model_routing_config.get("api_path")

    if api_path and provider_endpoint:
        effective_endpoint = provider_endpoint.rstrip("/") + api_path
    else:
        effective_endpoint = provider_endpoint

    # 3. Whether the model routes through the global LiteLLM Router
    via_router = is_model_in_router(model_system_name)

    # 4. Computed URL — best-effort approximation of what LiteLLM will call
    computed_url = _build_computed_url(
        provider_type=provider_type,
        model_name=model_name,
        endpoint=effective_endpoint,
        connection_config=connection_config,
        model_type=model_type,
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
    model_type: str | None = None,
) -> str | None:
    """Build the approximate full URL that LiteLLM will send requests to."""

    is_rerank = model_type == "re-ranking"
    is_embedding = model_type == "embeddings"

    if provider_type == "azure_open_ai":
        base = (endpoint or "").rstrip("/")
        if not base:
            return None
        api_version = connection_config.get("api_version", "2024-02-01")
        if is_embedding:
            return (
                f"{base}/openai/deployments/{model_name}"
                f"/embeddings?api-version={api_version}"
            )
        return (
            f"{base}/openai/deployments/{model_name}"
            f"/chat/completions?api-version={api_version}"
        )

    if provider_type == "azure_ai":
        base = (endpoint or "").rstrip("/")
        if not base:
            return None
        api_version = connection_config.get("api_version", "2024-05-01-preview")
        if is_rerank:
            # LiteLLM appends /rerank when base ends with a version path (/v1, /v2, /providers/cohere/v2)
            # otherwise defaults to /v1/rerank
            for version_suffix in ("/providers/cohere/v2", "/v2", "/v1"):
                if base.endswith(version_suffix):
                    return f"{base}/rerank"
            return f"{base}/v1/rerank"
        if is_embedding:
            return f"{base}/v1/embeddings"
        return f"{base}/chat/completions?api-version={api_version}"

    base = endpoint or _DEFAULT_BASE_URLS.get(provider_type)
    if not base:
        return None

    if is_rerank:
        return f"{base.rstrip('/')}/v1/rerank"
    if is_embedding:
        return f"{base.rstrip('/')}/v1/embeddings"
    return f"{base.rstrip('/')}/v1/chat/completions"
