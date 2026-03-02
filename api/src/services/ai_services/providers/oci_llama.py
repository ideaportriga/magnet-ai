"""
OCI GenAI Provider — Llama / Generic Chat models.

Supports:
- OCI Generative AI (Llama, Mistral, etc. via GenericChatRequest)
- routing_config for caching and retry
"""

import logging
from typing import Any

import oci
from openai.types.chat import ChatCompletionMessageParam

from services.ai_services.providers.base_oci import BaseOCIProvider

logger = logging.getLogger(__name__)


class OCILlamaProvider(BaseOCIProvider):
    """OCI provider for Llama/Generic models (GenericChatRequest API)."""

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
        system_message = next(
            (msg["content"] for msg in messages if msg["role"] == "system"),
            None,
        )

        oci_messages = [
            oci.generative_ai_inference.models.Message(
                role="SYSTEM",
                content=[
                    oci.generative_ai_inference.models.TextContent(text=system_message)
                ],
            ),
            oci.generative_ai_inference.models.Message(
                role="USER",
                content=[
                    oci.generative_ai_inference.models.TextContent(text=message_content)
                ],
            ),
        ]

        return oci.generative_ai_inference.models.GenericChatRequest(
            api_format=oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
            messages=oci_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=self.top_k,
            presence_penalty=0,
            frequency_penalty=self.frequency_penalty,
        )

    def _extract_response_content(self, response_data: Any) -> str:
        return response_data.chat_response.choices[0].message.content[0].text
