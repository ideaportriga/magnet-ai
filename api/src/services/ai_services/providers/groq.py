"""
Groq Provider using LiteLLM with routing_config support.

Supports:
- Groq models (llama, mixtral, gemma, etc.)
- Fast inference with Groq LPUs
- routing_config for caching, fallbacks, rate limiting
"""

from services.ai_services.providers.base_litellm import BaseLiteLLMProvider


class GroqProvider(BaseLiteLLMProvider):
    """
    Groq provider using LiteLLM.

    Configuration example:
    {
        "connection": {
            "api_key": "gsk_...",
            "endpoint": "https://api.groq.com/openai/v1"  # optional
        },
        "defaults": {
            "model": "llama-3.1-70b-versatile",
            "temperature": 0.7,
            "top_p": 1.0
        }
    }

    AIModel routing_config example:
    {
        "rpm": 30,
        "tpm": 14400,
        "fallback_models": ["llama-3.1-8b-instant"],
        "cache_enabled": true,
        "cache_ttl": 3600,
        "num_retries": 3,
        "timeout": 60
    }
    """

    litellm_provider = "groq"
