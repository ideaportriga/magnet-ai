"""
Local/Custom Provider using LiteLLM with routing_config support.

Supports:
- Local LLM endpoints (Ollama, vLLM, text-generation-inference, etc.)
- OpenAI-compatible custom endpoints
- routing_config for caching, fallbacks, rate limiting
"""

from typing import Any

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider


class TmpLocalProvider(BaseLiteLLMProvider):
    """
    Local/Custom endpoint provider using LiteLLM.

    For OpenAI-compatible local or custom endpoints.

    Configuration example:
    {
        "connection": {
            "api_key": "dummy-key",  # or actual key if required
            "endpoint": "http://localhost:8080/v1"
        },
        "defaults": {
            "model": "local-model",
            "temperature": 0.7,
            "top_p": 1.0
        }
    }

    AIModel routing_config example:
    {
        "cache_enabled": true,
        "cache_ttl": 3600,
        "num_retries": 2,
        "timeout": 300
    }
    """

    # No prefix for custom endpoints
    litellm_provider = ""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # For local endpoints, ensure we have a dummy key if none provided
        if not self.api_key:
            self.api_key = "sk-dummy-key"
