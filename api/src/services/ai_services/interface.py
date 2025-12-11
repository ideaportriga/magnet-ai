from abc import ABC, abstractmethod

from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from models import DocumentSearchResult
from services.ai_services.models import EmbeddingResponse, RerankResponse


class AIProviderInterface(ABC):
    @abstractmethod
    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> ChatCompletion:
        pass

    # Optional: Implement this method only if embeddings are supported
    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        raise NotImplementedError("get_embeddings is optional for this provider")

    # Optional: Implement this method only if rerank are supported
    async def rerank(
        self,
        query: str,
        documents: DocumentSearchResult,
        llm: str,
        top_n: int,
        truncation: bool | None,
    ) -> RerankResponse:
        raise NotImplementedError("rerank is optional for this provider")
