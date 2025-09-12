from typing import cast

import openai
from azure.ai.inference.aio import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage
from utils.common import transform_schema


class AzureProvider(AIProviderInterface):
    def __init__(self, config):
        self.api_key = config["connection"]["api_key"]
        self.endpoint = config["connection"]["endpoint"]
        self.api_version = config["connection"].get("api_version", "2023-03-15-preview")
        self.model_default = config["defaults"].get("model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")

    def _transform_messages_for_reasoning(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:
        """Transforms the list of messages for reasoning models:
        - Instructions that were previously provided via messages with the `system` role
          are now included directly in the prompt text.
        - If there are multiple messages with the `user` role, they are combined into a single prompt.
        - If desired, conversation history (e.g., assistant messages) can be preserved by adding prefixes.
        """
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                # Include instructions in the text without a prefix or add your own marker.
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(content)
            elif role == "assistant":
                # If you want to preserve the history, add a prefix (or you can ignore).
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(content)
        # Combine all parts, separating them with two newlines.
        combined_prompt = "\n\n".join(prompt_parts)
        # For the reasoning model, return a single message with the role "user".
        return [{"role": "user", "content": combined_prompt}]

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[ChatCompletionToolParam] | None = None,
        model_config: dict | None = None,
    ) -> ChatCompletion:
        model = model or self.model_default
        temperature = (
            temperature if temperature is not None else self.temperature_default
        )
        top_p = top_p if top_p is not None else self.top_p_default

        client = openai.AsyncAzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
        )

        if model_config and model_config.get("reasoning"):
            transformed_messages = self._transform_messages_for_reasoning(messages)
            reasoning_effort = model_config.get("reasoning_effort") or openai.NOT_GIVEN
            return await client.chat.completions.create(
                model=model,
                messages=transformed_messages,
                max_completion_tokens=max_tokens,
                response_format=transform_schema(response_format),
                tools=tools or openai.NOT_GIVEN,
                reasoning_effort=reasoning_effort,
            )

        # If not a reasoning model, use the original list of messages.
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=transform_schema(response_format),
            tools=tools or openai.NOT_GIVEN,
        )

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        if llm is None:
            raise ValueError("Model name must be provided")

        endpoint = f"{self.endpoint}/openai/deployments/{llm}"

        # Call the Azure API to get the embeddings.
        client = EmbeddingsClient(
            endpoint=endpoint, credential=AzureKeyCredential(key=self.api_key)
        )
        response = await client.embed(input=[text], model=llm)
        await client.close()

        return EmbeddingResponse(
            data=cast(list[float], response.data[0].embedding),
            usage=ModelUsage(
                input_units="tokens",
                input=response.usage.prompt_tokens,
                total=response.usage.total_tokens,
            ),
        )
