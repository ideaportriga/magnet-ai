import logging
import os
from decimal import Decimal
from typing import cast

import aiohttp
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
        # Default values
        self.model_default = config["defaults"].get("ai_model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")
        self.max_tokens = config["defaults"].get("max_tokens")

        self.timeout = config["connection"].get("timeout", 30_000)
        self.env_prefix = config["connection"]["env_prefix"]

        self.model_api_keys = self.get_model_configurations()

        # Create embedding clients for all models at initialization
        self._embedding_clients = {}
        self._create_embedding_clients()

    def get_model_configurations(self):
        model_configurations = {}

        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Extract the part after the prefix and split by underscore
                parts = key[len(self.env_prefix) :].split("_")

                if len(parts) == 2:
                    model_id = parts[
                        0
                    ]  # This will be the unique identifier (like "1" or "2")
                    attribute = parts[
                        1
                    ]  # This will be "DEPLOYMENT", "KEY", or "ENDPOINT"

                    # Check if the attribute is DEPLOYMENT
                    if attribute == "DEPLOYMENT":
                        # Initialize a new dictionary for this deployment if not already done
                        if value not in model_configurations:
                            model_configurations[value] = {
                                "key": None,
                                "endpoint": None,
                            }
                    elif attribute == "KEY":
                        # Fetch the deployment name and set the key
                        deployment = os.environ.get(
                            f"{self.env_prefix}{model_id}_DEPLOYMENT",
                        )
                        if deployment:
                            # Initialize if not already done
                            if deployment not in model_configurations:
                                model_configurations[deployment] = {
                                    "key": None,
                                    "endpoint": None,
                                }
                            model_configurations[deployment]["key"] = value
                    elif attribute == "ENDPOINT":
                        # Fetch the deployment name and set the endpoint
                        deployment = os.environ.get(
                            f"{self.env_prefix}{model_id}_DEPLOYMENT",
                        )
                        if deployment:
                            # Initialize if not already done
                            if deployment not in model_configurations:
                                model_configurations[deployment] = {
                                    "key": None,
                                    "endpoint": None,
                                }
                            model_configurations[deployment]["endpoint"] = value

        return model_configurations

    def _create_embedding_clients(self):
        """Create embedding clients for all configured models at initialization."""
        for model_name, config in self.model_api_keys.items():
            endpoint = config.get("endpoint")
            api_key = config.get("key")

            if endpoint and api_key:
                transport = AioHttpTransport(
                    connection_timeout=10,
                    read_timeout=30,
                )
                retry_policy = AsyncRetryPolicy(
                    retry_total=3,
                    retry_backoff_factor=0.8,
                )
                self._embedding_clients[model_name] = EmbeddingsClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(key=api_key),
                    transport=transport,
                    retry_policy=retry_policy,
                )

    def _get_embedding_client(self, llm: str) -> EmbeddingsClient:
        """Get the cached embedding client for the given model."""
        if llm not in self._embedding_clients:
            raise ValueError(
                f"Embedding client for model {llm} not found. Available models: {list(self._embedding_clients.keys())}"
            )

        return self._embedding_clients[llm]

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
            # TODO - add and test tools
        }

        modelConfig = self.model_api_keys.get(model)
        if not modelConfig:
            raise ValueError(f"Model {model} not found in configuration")
        endpoint = modelConfig.get("endpoint")
        api_key = modelConfig.get("key")
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout / 1000)
        ) as session:
            try:
                async with session.post(
                    endpoint, headers=headers, json=data
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

        # Get model config
        modelConfig = self.model_api_keys.get(llm)
        if not modelConfig:
            raise ValueError(f"Model {llm} not found in configuration")

        # Call the Azure API to get the embeddings
        client = self._get_embedding_client(llm)
        response = await client.embed(
            input=[text],
            model=llm,
            # this argument enables retry for embeding requests, do not remove it
            retry_on_methods=["POST"],
        )

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
        modelConfig = self.model_api_keys.get(llm)
        if not modelConfig:
            raise ValueError(f"Model {llm} not found in configuration")
        endpoint = modelConfig.get("endpoint")
        api_key = modelConfig.get("key")

        headers = {
            "Authorization": f"Bearer {api_key}",
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
                    endpoint,
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

    async def close(self):
        """Close all cached embedding clients to prevent connection leaks."""
        for client in self._embedding_clients.values():
            try:
                await client.close()
            except Exception as e:
                logger_azure.warning(f"Error closing embedding client: {e}")

        self._embedding_clients.clear()

    def __del__(self):
        """Cleanup method called when the object is being destroyed."""
        import asyncio

        # Try to close clients if there's an active event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule the cleanup task
            loop.create_task(self._cleanup_clients())
        except RuntimeError:
            # No event loop running, can't close async clients properly
            # Just clear the references
            self._embedding_clients.clear()

    async def _cleanup_clients(self):
        """Helper method to close all clients."""
        for client in self._embedding_clients.values():
            try:
                await client.close()
            except Exception as e:
                logger_azure.warning(f"Error closing embedding client: {e}")

        self._embedding_clients.clear()
