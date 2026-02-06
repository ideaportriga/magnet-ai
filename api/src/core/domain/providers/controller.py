from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.providers.service import (
    ProvidersService,
)
from core.domain.ai_models.service import AIModelsService

from .schemas import ProviderCreate, ProviderResponse, ProviderUpdate

if TYPE_CHECKING:
    pass


class ProviderTestResult(BaseModel):
    """Result of provider connection test."""

    success: bool = Field(..., description="Whether the test was successful")
    message: str = Field(..., description="Test result message")
    error: str | None = Field(None, description="Error details if test failed")


class ProviderAvailableModel(BaseModel):
    """Available model from provider."""

    id: str = Field(..., description="Model identifier")
    owned_by: str | None = Field(None, description="Model owner/provider")
    created: int | None = Field(None, description="Creation timestamp")
    # Inferred capabilities from LiteLLM
    model_type: str = Field(
        "prompts", description="Model type: prompts, embeddings, or image"
    )
    supports_function_calling: bool = Field(
        False, description="Supports function/tool calling"
    )
    supports_json_mode: bool = Field(False, description="Supports JSON mode")
    supports_response_schema: bool = Field(
        False, description="Supports response schema"
    )
    supports_vision: bool = Field(False, description="Supports vision/images")
    max_tokens: int | None = Field(None, description="Maximum tokens")


class ProviderAvailableModelsResponse(BaseModel):
    """Response with available models from provider."""

    models: list[ProviderAvailableModel] = Field(
        default_factory=list, description="List of available models"
    )
    source: str = Field(
        ...,
        description="Source: 'api' (from provider API) or 'litellm' (from LiteLLM registry)",
    )
    provider_type: str = Field(
        "", description="The provider type used for LiteLLM mapping"
    )
    error: str | None = Field(
        None, description="Error message if fetching from API failed"
    )


class ProvidersController(Controller):
    """Providers CRUD"""

    path = "/providers"
    tags = ["Admin / Providers"]

    dependencies = {
        **providers.create_service_dependencies(
            ProvidersService,
            "providers_service",
            filters={
                "pagination_type": "limit_offset",
                "id_filter": UUID,
                "search": "name",
                "search_ignore_case": True,
                "pagination_size": DEFAULT_PAGINATION_SIZE,
            },
        ),
        **providers.create_service_dependencies(
            AIModelsService,
            "ai_models_service",
        ),
    }

    @get()
    async def list_providers(
        self,
        providers_service: ProvidersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[ProviderResponse]:
        """List Providers with pagination and filtering."""
        results, total = await providers_service.list_and_count(*filters)
        return providers_service.to_schema(
            results, total, filters=filters, schema_type=ProviderResponse
        )

    @post()
    async def create_provider(
        self, providers_service: ProvidersService, data: ProviderCreate
    ) -> ProviderResponse:
        """Create a new Provider."""
        from services.ai_services.router import refresh_router

        obj = await providers_service.create(data)
        await refresh_router()  # Refresh LiteLLM router with new provider
        return providers_service.to_schema(obj, schema_type=ProviderResponse)

    @get("/code/{code:str}")
    async def get_provider_by_code(
        self, providers_service: ProvidersService, code: str
    ) -> ProviderResponse:
        """Get a Provider by its system_name."""
        obj = await providers_service.get_one(system_name=code)
        return providers_service.to_schema(obj, schema_type=ProviderResponse)

    @get("/{provider_id:uuid}")
    async def get_provider(
        self,
        providers_service: ProvidersService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to retrieve.",
        ),
    ) -> ProviderResponse:
        """Get a Provider by its ID."""
        obj = await providers_service.get(provider_id)
        return providers_service.to_schema(obj, schema_type=ProviderResponse)

    @patch("/{provider_id:uuid}")
    async def update_provider(
        self,
        providers_service: ProvidersService,
        data: ProviderUpdate,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to update.",
        ),
    ) -> ProviderResponse:
        """Update a Provider."""
        from services.ai_services.router import refresh_router

        obj = await providers_service.update(
            data, item_id=provider_id, auto_commit=True
        )
        await refresh_router()  # Refresh LiteLLM router with updated provider
        return providers_service.to_schema(obj, schema_type=ProviderResponse)

    @delete("/{provider_id:uuid}")
    async def delete_provider(
        self,
        providers_service: ProvidersService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to delete.",
        ),
    ) -> None:
        """Delete a Provider from the system."""
        from services.ai_services.router import refresh_router

        _ = await providers_service.delete(provider_id)
        await refresh_router()  # Refresh LiteLLM router after provider deletion

    @post(
        "/{provider_id:uuid}/test",
        summary="Test provider connection",
        status_code=HTTP_200_OK,
    )
    async def test_provider_connection(
        self,
        providers_service: ProvidersService,
        ai_models_service: AIModelsService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to test.",
        ),
    ) -> ProviderTestResult:
        """
        Test connection to a provider by making a simple API call.

        This endpoint verifies that the provider configuration is correct
        by attempting to initialize the provider client and make a basic request.
        """
        try:
            # Import here to avoid circular import
            from services.ai_services.factory import get_ai_provider

            # Get the provider from database
            provider = await providers_service.get(provider_id)
            if not provider:
                return ProviderTestResult(
                    success=False,
                    message="Provider not found",
                    error=f"Provider with ID {provider_id} does not exist",
                )

            # Try to get the AI provider instance (this tests the configuration)
            ai_provider = await get_ai_provider(provider.system_name)

            # Get models for this provider using AIModelsService
            provider_models = await ai_models_service.list(
                provider_system_name=provider.system_name
            )

            if not provider_models:
                return ProviderTestResult(
                    success=False,
                    message="No models configured for this provider",
                    error="Please add at least one model to the provider before testing",
                )

            # Find a suitable model for testing by type
            prompts_model = None
            embedding_model = None
            for model in provider_models:
                if model.type == "prompts" and not prompts_model:
                    prompts_model = model
                elif model.type == "embeddings" and not embedding_model:
                    embedding_model = model

            # Test with prompts model (chat completion) if available
            if prompts_model:
                try:
                    test_messages = [{"role": "user", "content": "Hi"}]
                    response = await ai_provider.create_chat_completion(
                        messages=test_messages,
                        model=prompts_model.ai_model,
                        temperature=0,
                        top_p=1,
                        max_tokens=5,  # Minimal tokens to save costs
                    )

                    if response and response.choices:
                        return ProviderTestResult(
                            success=True,
                            message=f"Connection successful! Provider '{provider.name}' is working correctly.",
                            error=None,
                        )
                    else:
                        return ProviderTestResult(
                            success=False,
                            message="Connection established but received unexpected response",
                            error="No response choices returned from provider",
                        )
                except NotImplementedError:
                    pass  # Try embedding model instead

            # Test with embedding model if no prompts model or prompts test failed
            if embedding_model:
                try:
                    response = await ai_provider.get_embeddings(
                        text="Test embedding",
                        llm=embedding_model.ai_model,
                    )

                    if response and response.data:
                        return ProviderTestResult(
                            success=True,
                            message=f"Connection successful! Provider '{provider.name}' is working correctly (tested via embeddings).",
                            error=None,
                        )
                    else:
                        return ProviderTestResult(
                            success=False,
                            message="Connection established but received unexpected response",
                            error="No embedding data returned from provider",
                        )
                except NotImplementedError:
                    pass

            # If we get here, no test succeeded
            return ProviderTestResult(
                success=False,
                message="Could not test provider",
                error="No suitable model type found for testing. Please add a prompts or embeddings model.",
            )

        except ValueError as e:
            return ProviderTestResult(
                success=False,
                message="Provider configuration error",
                error=str(e),
            )
        except Exception as e:
            return ProviderTestResult(
                success=False,
                message="Connection test failed",
                error=str(e),
            )

    @get(
        "/{provider_id:uuid}/available-models",
        summary="Get available models from provider",
        status_code=HTTP_200_OK,
    )
    async def get_available_models(
        self,
        providers_service: ProvidersService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The provider to get available models for.",
        ),
    ) -> ProviderAvailableModelsResponse:
        """
        Get available models from the provider.

        First tries to fetch models from the provider's API (if it supports /models endpoint).
        Falls back to LiteLLM's static model registry if API fetch fails.
        """
        from litestar.exceptions import NotFoundException
        import httpx
        import litellm

        def get_model_capabilities(model_id: str, provider_name: str) -> dict:
            """Get model capabilities from LiteLLM."""
            caps = {
                "model_type": "prompts",
                "supports_function_calling": False,
                "supports_json_mode": False,
                "supports_response_schema": False,
                "supports_vision": False,
                "max_tokens": None,
            }

            # Check if it's an embedding model
            if any(
                emb in model_id.lower()
                for emb in ["embed", "embedding", "text-embedding"]
            ):
                caps["model_type"] = "embeddings"
                return caps

            # Try to get info from LiteLLM with provider prefix
            model_key = f"{provider_name}/{model_id}" if provider_name else model_id
            try:
                model_info = litellm.get_model_info(model_key)
                # Use bool() to handle None values from LiteLLM
                caps["supports_function_calling"] = bool(
                    model_info.get("supports_function_calling")
                )
                caps["supports_json_mode"] = (
                    "response_format" in litellm.get_supported_openai_params(model_key)
                )
                caps["supports_response_schema"] = bool(
                    model_info.get("supports_response_schema")
                )
                caps["supports_vision"] = bool(model_info.get("supports_vision"))
                caps["max_tokens"] = model_info.get("max_tokens") or model_info.get(
                    "max_output_tokens"
                )
            except Exception:
                # Try without provider prefix
                try:
                    model_info = litellm.get_model_info(model_id)
                    caps["supports_function_calling"] = bool(
                        model_info.get("supports_function_calling")
                    )
                    caps["supports_json_mode"] = (
                        "response_format"
                        in litellm.get_supported_openai_params(model_id)
                    )
                    caps["supports_response_schema"] = bool(
                        model_info.get("supports_response_schema")
                    )
                    caps["supports_vision"] = bool(model_info.get("supports_vision"))
                    caps["max_tokens"] = model_info.get("max_tokens") or model_info.get(
                        "max_output_tokens"
                    )
                except Exception:
                    pass

            return caps

        provider = await providers_service.get(provider_id)
        if not provider:
            raise NotFoundException(f"Provider with ID {provider_id} not found")

        provider_type = provider.type or provider.system_name
        models = []
        source = "litellm"
        error_msg = None

        # Map provider type to LiteLLM provider name
        litellm_provider_map = {
            "openai": "openai",
            "azure_open_ai": "azure",
            "azure_ai": "azure_ai",
            "azure": "azure",
            "groq": "groq",
            "anthropic": "anthropic",
            "gemini": "gemini",
            "bedrock": "bedrock",
            "together_ai": "together_ai",
            "ollama": "ollama",
            "deepseek": "deepseek",
            "mistral": "mistral",
            "cohere": "cohere",
            "vertex_ai": "vertex_ai",
            "fireworks_ai": "fireworks_ai",
        }
        litellm_provider = litellm_provider_map.get(provider_type, provider_type)

        # Try to fetch from provider API if it has an endpoint
        if provider.endpoint:
            try:
                # Get API key from secrets (optional — some providers like LM Studio don't require it)
                secrets = provider.secrets_encrypted or {}
                api_key = (
                    secrets.get("api_key")
                    or secrets.get("openai_api_key")
                    or secrets.get("OPENAI_API_KEY")
                )

                # Build the models endpoint URL
                base_url = provider.endpoint.rstrip("/")
                models_url = f"{base_url}/models"

                headers = {
                    "Content-Type": "application/json",
                }
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"

                # Use verify=False for localhost/local network endpoints (e.g. LM Studio)
                is_local = any(
                    h in base_url
                    for h in [
                        "localhost",
                        "127.0.0.1",
                        "0.0.0.0",
                        "host.docker.internal",
                    ]
                )

                async with httpx.AsyncClient(
                    timeout=15.0, verify=not is_local
                ) as client:
                    response = await client.get(models_url, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        # OpenAI-compatible format: {"data": [...], "object": "list"}
                        model_list = (
                            data.get("data", []) if isinstance(data, dict) else data
                        )

                        if isinstance(model_list, list) and len(model_list) > 0:
                            for m in model_list:
                                if isinstance(m, dict):
                                    model_id = m.get("id", "")
                                    if not model_id:
                                        continue
                                    caps = get_model_capabilities(
                                        model_id, litellm_provider
                                    )
                                    models.append(
                                        ProviderAvailableModel(
                                            id=model_id,
                                            owned_by=m.get("owned_by"),
                                            created=m.get("created"),
                                            **caps,
                                        )
                                    )

                            source = "api"
                    else:
                        error_msg = (
                            f"Provider API returned status {response.status_code}"
                        )
            except Exception as e:
                error_msg = f"Could not fetch from provider API: {str(e)}"

        # Fallback to LiteLLM static registry
        if not models and hasattr(litellm, "models_by_provider"):
            if litellm_provider in litellm.models_by_provider:
                for model_id in litellm.models_by_provider[litellm_provider]:
                    # Skip image generation models and other non-chat models
                    if any(
                        skip in model_id
                        for skip in ["dall-e", "tts-", "whisper-", "moderation"]
                    ):
                        continue
                    caps = get_model_capabilities(model_id, litellm_provider)
                    models.append(
                        ProviderAvailableModel(
                            id=model_id,
                            owned_by=litellm_provider,
                            created=None,
                            **caps,
                        )
                    )

        return ProviderAvailableModelsResponse(
            models=models,
            source=source,
            provider_type=litellm_provider,
            error=error_msg,
        )
