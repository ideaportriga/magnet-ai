"""
Azure OpenAI Provider using LiteLLM with routing_config support.

Supports:
- Azure OpenAI deployments
- Embeddings
- routing_config for caching, fallbacks, rate limiting
"""

from typing import Any

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider


class AzureProvider(BaseLiteLLMProvider):
    """
    Azure OpenAI provider using LiteLLM.

    Configuration example:
    {
        "connection": {
            "api_key": "...",
            "endpoint": "https://your-resource.openai.azure.com/",
            "api_version": "2024-02-01"
        },
        "defaults": {
            "model": "gpt-4o-deployment",  # deployment name
            "temperature": 0.7,
            "top_p": 1.0
        }
    }

    AIModel routing_config example:
    {
        "rpm": 1000,
        "tpm": 100000,
        "fallback_models": ["gpt-4o-mini-deployment"],
        "cache_enabled": true,
        "cache_ttl": 3600,
        "num_retries": 3,
        "timeout": 120
    }
    """

    litellm_provider = "azure"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Azure requires api_version
        if not self.api_version:
            self.api_version = "2024-02-01"

    def _build_litellm_params(self) -> dict[str, Any]:
        """Build Azure-specific LiteLLM parameters."""
        params = super()._build_litellm_params()

        # Azure uses azure_endpoint instead of api_base
        if self.endpoint:
            params["api_base"] = self.endpoint

        return params
