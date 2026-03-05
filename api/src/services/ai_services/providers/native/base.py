"""
Base class for native providers that bypass LiteLLM.

Use this for providers/operations not supported by LiteLLM, such as:
- Mistral Voxtral STT (with diarization)
- OCI Speech diarization
- Custom proprietary APIs

Native providers still integrate with the ai_services framework:
- Credentials come from Provider entity in DB (not env vars)
- Registered in factory.py like any other provider
- Implement AIProviderInterface for uniform access

Decision tree:
    Model/operation needed
    ├─ Supported by LiteLLM? → UniversalLiteLLMProvider ✅
    └─ NOT supported? → Need unique features (diarization, custom params)?
       ├─ NO → Register CustomLLM with litellm
       └─ YES → Create native provider inheriting BaseNativeProvider
"""

import logging
from typing import Any

from services.ai_services.interface import AIProviderInterface

logger = logging.getLogger(__name__)


class BaseNativeProvider(AIProviderInterface):
    """
    Base for providers that bypass LiteLLM and call APIs directly.

    Provides common initialization (api_key, endpoint, defaults)
    from the Provider entity configuration.

    Subclasses should implement the relevant methods (transcribe, speech, etc.)
    and raise NotImplementedError for unsupported operations.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        connection = config.get("connection", {})
        defaults = config.get("defaults", {})

        self.api_key = connection.get("api_key")
        self.endpoint = connection.get("endpoint")
        self.default_model = defaults.get("model")

        # Optional timeout from connection config (in seconds)
        self.timeout = connection.get("timeout", 300)

    async def create_chat_completion(self, *args, **kwargs):
        """Native providers typically don't support chat completion."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support chat completion. "
            "Use the appropriate method (transcribe, speech, etc.)"
        )
