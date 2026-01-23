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
        obj = await providers_service.create(data)
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
        obj = await providers_service.update(
            data, item_id=provider_id, auto_commit=True
        )
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
        _ = await providers_service.delete(provider_id)

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
