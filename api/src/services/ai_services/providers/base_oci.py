"""
Base OCI GenAI Provider with shared initialization and caching.

Provides common logic for all OCI-based providers:
- Client initialization with OCI config
- Response caching with routing_config support
- Async execution via run_in_executor
- Message extraction helpers
"""

import asyncio
import logging
import time
from abc import abstractmethod
from copy import deepcopy
from typing import Any

import oci
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from services.ai_services.cache import response_cache
from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage

logger = logging.getLogger(__name__)


class BaseOCIProvider(AIProviderInterface):
    """Base class for OCI GenAI providers.

    Handles client initialization, caching, and async execution.
    Subclasses implement _build_chat_request() and _extract_response_content().
    """

    def __init__(self, config: dict[str, Any]):
        connection = config["connection"]
        defaults = config.get("defaults", {})

        self.compartment_id = connection["compartment_id"]
        self.model_default = defaults.get("model")
        self.temperature_default = defaults.get("temperature")
        self.top_p_default = defaults.get("top_p")
        self.max_tokens = defaults.get("max_tokens")
        self.frequency_penalty = defaults.get("frequency_penalty")
        self.top_k = defaults.get("top_k")

        key_content = connection["key_content"].replace("\\n", "\n")
        self.oci_config = {
            "user": connection["user"],
            "fingerprint": connection["fingerprint"],
            "tenancy": connection["tenancy"],
            "region": connection["region"],
            "key_content": key_content,
        }
        self.endpoint = connection["endpoint"]

        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=self.oci_config,
            service_endpoint=self.endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

    @abstractmethod
    def _build_chat_request(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None,
    ) -> Any:
        """Build the OCI-specific chat request object.

        Returns an OCI chat request (CohereChatRequest, GenericChatRequest, etc.)
        """
        ...

    @abstractmethod
    def _extract_response_content(self, response_data: Any) -> str:
        """Extract text content from OCI chat response data."""
        ...

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> ChatCompletion:
        model = model or self.model_default
        temperature = temperature or self.temperature_default
        top_p = top_p or self.top_p_default
        max_tokens = max_tokens or self.max_tokens

        # Extract routing_config for caching support
        routing_config = (model_config or {}).get("routing_config") or {}

        # Check cache if enabled
        cache_enabled = routing_config.get("cache_enabled", False)
        cache_key = None
        if cache_enabled:
            cache_key = response_cache.make_key(
                model=model,
                messages=str(messages),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            cached = response_cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for OCI model {model}")
                # Return copy with zeroed usage to avoid double billing
                cached_copy = deepcopy(cached)
                if hasattr(cached_copy, "usage") and cached_copy.usage:
                    cached_copy.usage.prompt_tokens = 0
                    cached_copy.usage.completion_tokens = 0
                    cached_copy.usage.total_tokens = 0
                return cached_copy

        # Build OCI-specific chat request (delegated to subclass)
        chat_request = self._build_chat_request(
            messages, model, temperature, top_p, max_tokens
        )

        chat_detail = oci.generative_ai_inference.models.ChatDetails(
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=model,
            ),
            chat_request=chat_request,
            compartment_id=self.compartment_id,
        )

        try:
            loop = asyncio.get_running_loop()
            chat_response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(chat_detail),
            )
        except oci.exceptions.ServiceError as e:
            logger.error("OCI service error: %s", e)
            raise

        if not chat_response:
            raise Exception("No response from OCI for chat API")

        data = chat_response.data
        content = self._extract_response_content(data)
        model_id = data.model_id

        result = ChatCompletion(
            id="oci_completion",
            object="chat.completion",
            created=int(time.time()),
            model=model_id,
            choices=[
                Choice(
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=content,
                    ),
                    finish_reason="stop",
                    index=0,
                ),
            ],
        )

        # Cache the result if caching is enabled
        if cache_key:
            cache_ttl = routing_config.get("cache_ttl", 3600)
            response_cache.set(cache_key, result, ttl=cache_ttl)

        return result

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        """Get embeddings using the shared OCI client."""
        embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
        embed_text_detail.serving_mode = (
            oci.generative_ai_inference.models.OnDemandServingMode(model_id=llm)
        )
        embed_text_detail.inputs = [text]
        embed_text_detail.truncate = "NONE"
        embed_text_detail.compartment_id = self.compartment_id

        loop = asyncio.get_running_loop()
        embed_text_response = await loop.run_in_executor(
            None,
            lambda: self.client.embed_text(embed_text_detail),
        )

        if not embed_text_response:
            raise Exception("No response from OCI for embeddings API")

        usage_in_characters = len(text)

        return EmbeddingResponse(
            data=embed_text_response.data.embeddings,
            usage=ModelUsage(
                input_units="characters",
                input=usage_in_characters,
                total=usage_in_characters,
            ),
        )
