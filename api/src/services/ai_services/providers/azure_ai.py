"""
Azure AI Inference Provider using LiteLLM with routing_config support.

Supports:
- Azure AI Inference models (Mistral, Llama, Phi, etc.)
- Models deployed via Azure AI Studio
- Embeddings and Reranking
- routing_config for caching, fallbacks, rate limiting
"""

from typing import Any

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider


class AzureAIProvider(BaseLiteLLMProvider):
    """
    Azure AI Inference provider using LiteLLM.

    For models deployed via Azure AI Studio (not Azure OpenAI).

    Configuration example:
    {
        "connection": {
            "api_key": "...",
            "endpoint": "https://your-model.eastus.inference.ai.azure.com/",
            "api_version": "2024-05-01-preview"
        },
        "defaults": {
            "model": "mistral-large",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 4096
        }
    }

    AIModel routing_config example:
    {
        "rpm": 500,
        "tpm": 50000,
        "fallback_models": ["mistral-small"],
        "cache_enabled": true,
        "cache_ttl": 3600,
        "num_retries": 3,
        "timeout": 120
    }
    """

    litellm_provider = "azure_ai"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Azure AI uses different api_version
        if not self.api_version:
            self.api_version = "2024-05-01-preview"

        # Store timeout from connection config
        self.timeout = (
            self.connection.get("timeout", 30000) / 1000
        )  # convert to seconds
