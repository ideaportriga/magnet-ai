import openai
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.interface import AIProviderInterface
from utils.common import transform_schema


class GroqProvider(AIProviderInterface):
    def __init__(self, config):
        # Connection parameters
        self.api_key = config["connection"]["api_key"]
        self.endpoint = config["connection"]["endpoint"]

        # Default parameters
        self.model_default = config["defaults"].get("model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")
        # Client init
        self.client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.endpoint)

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        model_config: dict | None = None,
    ) -> ChatCompletion:
        model = model or self.model_default
        temperature = temperature or self.temperature_default
        top_p = top_p or self.top_p_default

        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            response_format=transform_schema(response_format),
        )
