"""
Universal LiteLLM Provider — single class supporting all LiteLLM-backed providers.

Replaces individual provider classes (OpenAIProvider, AzureProvider, GroqProvider, etc.)
with one dynamic class that determines the litellm_provider prefix from the provider type.

This eliminates the need to create a new file for each new LLM provider.
Adding a new provider is now just a DB entry — no code changes required.
"""

import logging
from typing import Any

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider

logger = logging.getLogger(__name__)

# Mapping: provider.type → litellm model prefix
# See https://docs.litellm.ai/docs/providers for full list
PROVIDER_TYPE_TO_LITELLM_PREFIX: dict[str, str] = {
    # Major cloud providers
    "openai": "openai",
    "azure_open_ai": "azure",
    "azure_ai": "azure_ai",
    "bedrock": "bedrock",
    "vertex_ai": "vertex_ai",
    # Inference providers
    "groq": "groq",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "mistral": "mistral",
    "cohere": "cohere",
    "deepseek": "deepseek",
    "fireworks_ai": "fireworks_ai",
    "together_ai": "together_ai",
    "perplexity": "perplexity",
    "xai": "xai",
    "ai21": "ai21",
    "cerebras": "cerebras",
    "sambanova": "sambanova",
    "friendliai": "friendliai",
    "openrouter": "openrouter",
    # Self-hosted / custom
    "ollama": "ollama",
    "vllm": "hosted_vllm",
    "lm_studio": "lm_studio",
    "text_completion_openai": "text-completion-openai",
    # Audio / multimodal
    "elevenlabs": "elevenlabs",
    "deepgram": "deepgram",
    # OCI through litellm (alternative to native OCI SDK)
    "oci_genai": "oci_genai",
    # Custom / OpenAI-compatible endpoints (no prefix)
    "datakom": "",
    "litellm": "",  # model already has prefix
    "custom": "",
}


class UniversalLiteLLMProvider(BaseLiteLLMProvider):
    """
    Single provider class supporting all LiteLLM-backed providers.

    Instead of separate OpenAIProvider, AzureProvider, GroqProvider, etc.,
    this class dynamically determines the litellm_provider prefix from
    the provider type stored in the database.

    Adding a new provider requires only:
    1. Add a row to PROVIDER_TYPE_TO_LITELLM_PREFIX (if not already there)
    2. Create Provider + Model entries in the database

    Configuration example:
    {
        "type": "anthropic",
        "connection": {
            "api_key": "sk-ant-...",
            "endpoint": null
        },
        "defaults": {
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7
        }
    }
    """

    def __init__(self, config: dict[str, Any]):
        # Determine litellm prefix from provider type
        provider_type = config.get("type", "")
        self.litellm_provider = PROVIDER_TYPE_TO_LITELLM_PREFIX.get(
            str(provider_type), ""
        )

        if provider_type and provider_type not in PROVIDER_TYPE_TO_LITELLM_PREFIX:
            logger.warning(
                "Unknown provider type '%s' — using empty prefix (OpenAI-compatible mode). "
                "Consider adding it to PROVIDER_TYPE_TO_LITELLM_PREFIX.",
                provider_type,
            )

        super().__init__(config)

        # Provider-type-specific defaults
        self._apply_provider_defaults(provider_type)

    def _apply_provider_defaults(self, provider_type: str) -> None:
        """Apply default settings specific to certain provider types."""
        if provider_type == "azure_open_ai":
            if not self.api_version:
                self.api_version = "2024-02-01"

        elif provider_type == "azure_ai":
            if not self.api_version:
                self.api_version = "2024-05-01-preview"
            # Azure AI stores timeout in ms in connection config
            timeout_ms = self.connection.get("timeout")
            if timeout_ms is not None:
                self.timeout = timeout_ms / 1000  # convert to seconds

        elif provider_type in ("datakom", "custom", ""):
            # For custom/local endpoints, ensure we have a dummy key if none provided
            if not self.api_key:
                self.api_key = "sk-dummy-key"

    def _build_litellm_params(self) -> dict[str, Any]:
        """Build LiteLLM parameters with provider-specific handling."""
        params = super()._build_litellm_params()

        # Azure uses api_base for endpoints
        provider_type = self.config.get("type", "")
        if provider_type == "azure_open_ai" and self.endpoint:
            params["api_base"] = self.endpoint

        return params
