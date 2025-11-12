import logging
from decimal import Decimal
from typing import cast

import aiohttp
from utils.common import transform_schema
from azure.ai.inference.aio import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline.policies import AsyncRetryPolicy
from azure.core.pipeline.transport import AioHttpTransport
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from models import DocumentSearchResult
from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage, RerankResponse

logger_azure = logging.getLogger("azure")
logger_azure.setLevel(logging.WARNING)


class AzureAIProvider(AIProviderInterface):
    def __init__(self, config):
        # Connection configuration
        self.api_key = config["connection"]["api_key"]
        self.endpoint = config["connection"]["endpoint"]
        self.api_version = config["connection"].get("api_version", "2025-01-01-preview")
        
        # Default values
        self.model_default = config["defaults"].get("ai_model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")
        self.max_tokens = config["defaults"].get("max_tokens")

        self.timeout = config["connection"].get("timeout", 30_000)

    def _get_embedding_client(self, llm: str) -> EmbeddingsClient:
        """Get embedding client for the given model (deployment name)."""
        transport = AioHttpTransport(
            connection_timeout=10,
            read_timeout=30,
        )
        retry_policy = AsyncRetryPolicy(
            retry_total=3,
            retry_backoff_factor=0.8,
        )
        
        # Construct endpoint for specific deployment/model with API version
        model_endpoint = f"{self.endpoint}/openai/deployments/{llm}?api-version={self.api_version}"
        
        return EmbeddingsClient(
            endpoint=model_endpoint,
            credential=AzureKeyCredential(key=self.api_key),
            transport=transport,
            retry_policy=retry_policy,
        )

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        model_config: dict | None = None,
    ) -> ChatCompletion:
        model = model or self.model_default
        temperature = temperature or self.temperature_default
        top_p = top_p or self.top_p_default
        max_tokens = max_tokens or self.max_tokens

        data = {
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "model": model,
        }

        if response_format:
            data["response_format"] = transform_schema(response_format)

        if tools:
            data["tools"] = tools

        # Construct endpoint for specific model/deployment with API version
        model_endpoint = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"
        headers = {"api-key": self.api_key}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout / 1000)
        ) as session:
            try:
                async with session.post(
                    model_endpoint, headers=headers, json=data
                ) as response:
                    response_json = await response.json()
                    response.raise_for_status()
            except aiohttp.ContentTypeError:
                raise
            except aiohttp.ClientResponseError as e:
                logger_azure.error(e)
                raise Exception(response_json)

        completion = ChatCompletion(**response_json)

        return completion

    async def get_embeddings(
        self,
        text: str,
        chunk_size: int | None = 0,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        if llm is None:
            raise ValueError("Model name must be provided")

        # Call the Azure API to get the embeddings
        client = self._get_embedding_client(llm)
        response = await client.embed(
            input=[text],
            model=llm,
            # this argument enables retry for embeding requests, do not remove it
            retry_on_methods=["POST"],
        )
        await client.close()

        return EmbeddingResponse(
            data=cast(list[float], response.data[0].embedding),
            usage=ModelUsage(
                input_units="tokens",
                input=response.usage.prompt_tokens,
                total=response.usage.total_tokens,
            ),
        )

    async def rerank(
        self,
        query: str,
        documents: DocumentSearchResult,
        llm: str,
        top_n: int,
        truncation: bool,
    ) -> RerankResponse:
        # Construct endpoint for specific model/deployment with API version
        model_endpoint = f"{self.endpoint}/openai/deployments/{llm}/rerank?api-version={self.api_version}"
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "query": query,
            "documents": [
                {
                    "title": doc.metadata.get("title", "Unknown Title"),
                    "content": doc.content,
                }
                for doc in documents
            ],
            "rank_fields": ["content", "title"],
            "top_n": top_n,
            "model": llm,
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout / 1000),
        ) as session:
            try:
                async with session.post(
                    model_endpoint,
                    headers=headers,
                    json=data,
                ) as response:
                    response.raise_for_status()
                    response_json = await response.json()
            except Exception as e:
                logger_azure.error(f"Error in rerank: {e}")
                raise

        # Currently, Azure supports only Cohere rerank model, so we can only get the usage in queries
        if "meta" in response_json and "billed_units" in response_json["meta"]:
            search_units = response_json["meta"]["billed_units"].get("search_units", 1)
            usage = ModelUsage(
                input_units="queries",
                input=search_units,
                total=search_units,
            )
        else:
            usage = None

        # Convert response to a dictionary with index as key and score as value
        new_scores = {
            doc_result["index"]: doc_result["relevance_score"]
            for doc_result in response_json.get("results", [])
        }

        # Create new array of documents with new scores
        reranked_documents = []
        for index, doc in enumerate(documents):
            doc.score = Decimal(new_scores.get(index, doc.score))
            doc.original_index = index
            reranked_documents.append(doc)

        return RerankResponse(data=reranked_documents, usage=usage)
