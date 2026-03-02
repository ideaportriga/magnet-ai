"""
OpenAI Provider using LiteLLM with routing_config support.

Supports:
- OpenAI models (gpt-4o, gpt-4o-mini, o1, o3-mini, etc.)
- OpenAI-compatible endpoints (custom base_url)
- Embeddings (text-embedding-3-small, text-embedding-3-large)
- Reranking
- routing_config for caching, fallbacks, rate limiting
"""

from typing import Any

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider


class OpenAIProvider(BaseLiteLLMProvider):
    """
    OpenAI provider using LiteLLM.

    Configuration example:
    {
        "connection": {
            "api_key": "sk-...",
            "endpoint": "https://api.openai.com/v1"  # optional, for custom endpoints
        },
        "defaults": {
            "model": "gpt-4o",
            "temperature": 0.7,
            "top_p": 1.0
        }
    }

    AIModel routing_config example:
    {
        "rpm": 500,
        "tpm": 100000,
        "fallback_models": ["gpt-4o-mini"],
        "cache_enabled": true,
        "cache_ttl": 3600,
        "num_retries": 3,
        "timeout": 120
    }
    """

    litellm_provider = "openai"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
