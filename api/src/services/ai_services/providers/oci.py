"""
OCI GenAI Provider — Cohere Command models.

Supports:
- OCI Generative AI (Cohere Command models)
- Embeddings
- routing_config for caching and retry
"""

from typing import Any

import oci
from openai.types.chat import ChatCompletionMessageParam

from services.ai_services.providers.base_oci import BaseOCIProvider


class OCIProvider(BaseOCIProvider):
    """OCI provider for Cohere Command models (CohereChatRequest API)."""

    def _build_chat_request(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None,
    ) -> Any:
        message_content = next(
            (msg["content"] for msg in messages if msg["role"] == "user"),
            None,
        )
        preamble_override = next(
            (msg["content"] for msg in messages if msg["role"] == "system"),
            None,
        )

        chat_request = oci.generative_ai_inference.models.CohereChatRequest()
        chat_request.message = message_content
        chat_request.max_tokens = max_tokens
        chat_request.temperature = temperature
        chat_request.top_p = top_p
        chat_request.top_k = self.top_k
        chat_request.preamble_override = preamble_override
        chat_request.frequency_penalty = self.frequency_penalty

        return chat_request

    def _extract_response_content(self, response_data: Any) -> str:
        return response_data.chat_response.text
