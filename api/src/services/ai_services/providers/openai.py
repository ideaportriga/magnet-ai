import openai
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage
from utils.common import transform_schema


class OpenAIProvider(AIProviderInterface):
    def __init__(self, config):
        self.api_key = config["connection"].get("api_key")
        self.endpoint = config["connection"].get("endpoint")
        self.model_default = config["defaults"].get("model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")

        # Create client with custom endpoint if provided
        # For local endpoints without API key, use a dummy key
        api_key = self.api_key or "sk-dummy-key"

        if self.endpoint:
            self.client = openai.AsyncOpenAI(api_key=api_key, base_url=self.endpoint)
        else:
            self.client = openai.AsyncOpenAI(api_key=api_key)

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
        temperature = (
            temperature if temperature is not None else self.temperature_default
        )
        top_p = top_p if top_p is not None else self.top_p_default

        params = {
            "model": model,
            "messages": messages,
            "top_p": top_p if top_p is not None else openai.NOT_GIVEN,
            "max_completion_tokens": max_tokens or openai.NOT_GIVEN,
            "response_format": transform_schema(response_format),
        }

        if model_config and model_config.get("reasoning"):
            params["reasoning_effort"] = model_config.get("reasoning_effort") or "low"
        else:
            params["temperature"] = (
                temperature if temperature is not None else openai.NOT_GIVEN
            )

        # if model_config and model_config.get("tool_calling"):
        params["tools"] = tools or openai.NOT_GIVEN
        params["tool_choice"] = tool_choice or openai.NOT_GIVEN

        if tools:
            params["parallel_tool_calls"] = (
                parallel_tool_calls
                if parallel_tool_calls is not None
                else openai.NOT_GIVEN
            )

        return await self.client.chat.completions.create(**params)

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        if llm is None:
            raise ValueError("Model name must be provided")

        response = await self.client.embeddings.create(
            model=llm,
            input=text,
        )

        return EmbeddingResponse(
            data=response.data[0].embedding,
            usage=ModelUsage(
                input_units="tokens",
                input=response.usage.prompt_tokens,
                total=response.usage.total_tokens,
            ),
        )
