from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import BinaryIO

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
)

from models import DocumentSearchResult
from services.ai_services.models import (
    EmbeddingResponse,
    ImageGenerationResult,
    RerankResponse,
    ResponsesAPIResult,
    TranscriptionResponse,
)
from typing import Any


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

    async def create_chat_completion_stream(
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
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Stream chat completion chunks. Override in subclasses that support streaming."""
        raise NotImplementedError("Streaming is not supported by this provider")
        # Make this an async generator so the return type annotation is correct
        yield  # pragma: no cover  # noqa: E501

    # Optional: Implement this method only if embeddings are supported
    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
        model_config: dict | None = None,
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
        model_config: dict | None = None,
    ) -> RerankResponse:
        raise NotImplementedError("rerank is optional for this provider")

    # Optional: Implement for STT support
    async def transcribe(
        self,
        file: BinaryIO,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str | None = None,
        timestamp_granularities: list[str] | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> TranscriptionResponse:
        """Transcribe audio. Override in subclasses that support STT."""
        raise NotImplementedError("transcribe is optional for this provider")

    # Optional: Implement for TTS support
    async def speech(
        self,
        input: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,
        speed: float | None = None,
    ) -> bytes:
        """Generate speech audio. Override in subclasses that support TTS."""
        raise NotImplementedError("speech is optional for this provider")

    # Optional: Responses API (OpenAI /v1/responses, Codex, web search)
    async def create_response(
        self,
        input: str | list,
        model: str | None = None,
        instructions: str | None = None,
        tools: list | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        tool_choice: str | dict | None = None,
        previous_response_id: str | None = None,
        background: bool | None = None,
        reasoning: dict | None = None,
        text_format: dict | type | None = None,
        model_config: dict | None = None,
        **kwargs,
    ) -> ResponsesAPIResult:
        """Create a response using the Responses API. Override in subclasses."""
        raise NotImplementedError("create_response is optional for this provider")

    async def create_response_stream(
        self,
        input: str | list,
        model: str | None = None,
        instructions: str | None = None,
        tools: list | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        tool_choice: str | dict | None = None,
        previous_response_id: str | None = None,
        reasoning: dict | None = None,
        text_format: dict | type | None = None,
        model_config: dict | None = None,
        **kwargs,
    ) -> AsyncIterator:
        """Stream a Responses API response. Override in subclasses."""
        raise NotImplementedError(
            "create_response_stream is optional for this provider"
        )
        yield  # pragma: no cover

    # Optional: Image generation
    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        n: int = 1,
        size: str | None = None,
        quality: str | None = None,
        style: str | None = None,
        response_format: str | None = None,
    ) -> ImageGenerationResult:
        """Generate images from text. Override in subclasses."""
        raise NotImplementedError("generate_image is optional for this provider")
