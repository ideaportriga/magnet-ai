from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.ai_models.service import (
    AIModelsService,
)
from openai_model.utils import clear_model_cache

from .schemas import AIModel, AIModelCreate, AIModelSetDefaultRequest, AIModelUpdate

if TYPE_CHECKING:
    pass

logger = getLogger(__name__)


class ModelTestResult(BaseModel):
    """Result of model test."""

    success: bool = Field(..., description="Whether the test was successful")
    message: str = Field(..., description="Test result message")
    error: str | None = Field(None, description="Error details if test failed")
    response_preview: str | None = Field(
        None, description="Preview of model response if successful"
    )


class ModelCapabilities(BaseModel):
    """Model capabilities and supported parameters from LiteLLM."""

    supported_params: list[str] = Field(
        default_factory=list, description="Supported OpenAI parameters"
    )
    max_tokens: int | None = Field(None, description="Maximum total tokens")
    max_input_tokens: int | None = Field(None, description="Maximum input tokens")
    max_output_tokens: int | None = Field(None, description="Maximum output tokens")
    supports_vision: bool = Field(
        False, description="Whether model supports vision/images"
    )
    supports_function_calling: bool = Field(
        False, description="Whether model supports function calling"
    )
    supports_response_schema: bool = Field(
        False, description="Whether model supports response schema"
    )
    supports_audio_input: bool = Field(
        False, description="Whether model supports audio input"
    )
    supports_audio_output: bool = Field(
        False, description="Whether model supports audio output"
    )
    input_cost_per_token: float | None = Field(None, description="Input cost per token")
    output_cost_per_token: float | None = Field(
        None, description="Output cost per token"
    )


class AIModelsController(Controller):
    """AI Models CRUD"""

    path = "/models"
    tags = ["Admin / Models"]

    dependencies = providers.create_service_dependencies(
        AIModelsService,
        "ai_models_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_ai_models(
        self,
        ai_models_service: AIModelsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[AIModel]:
        """List AI models with pagination and filtering."""
        results, total = await ai_models_service.list_and_count(*filters)
        return ai_models_service.to_schema(
            results, total, filters=filters, schema_type=AIModel
        )

    @post()
    async def create_ai_model(
        self, ai_models_service: AIModelsService, data: AIModelCreate
    ) -> AIModel:
        """Create a new AI model."""
        from services.ai_services.router import refresh_router

        obj = await ai_models_service.create(data)
        clear_model_cache()
        await refresh_router()  # Refresh LiteLLM router with new model
        return ai_models_service.to_schema(obj, schema_type=AIModel)

    @get("/code/{code:str}")
    async def get_ai_model_by_code(
        self, ai_models_service: AIModelsService, code: str
    ) -> AIModel:
        """Get an AI model by its system_name."""
        obj = await ai_models_service.get_one(system_name=code)
        return ai_models_service.to_schema(obj, schema_type=AIModel)

    @get("/{ai_model_id:uuid}")
    async def get_ai_model(
        self,
        ai_models_service: AIModelsService,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to retrieve.",
        ),
    ) -> AIModel:
        """Get an AI model by its ID."""
        obj = await ai_models_service.get(ai_model_id)
        return ai_models_service.to_schema(obj, schema_type=AIModel)

    @patch("/{ai_model_id:uuid}")
    async def update_ai_model(
        self,
        ai_models_service: AIModelsService,
        data: AIModelUpdate,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to update.",
        ),
    ) -> AIModel:
        """Update an AI model."""
        from services.ai_services.router import refresh_router

        obj = await ai_models_service.update(
            data, item_id=ai_model_id, auto_commit=True
        )
        clear_model_cache()
        await refresh_router()  # Refresh LiteLLM router with updated model
        return ai_models_service.to_schema(obj, schema_type=AIModel)

    @delete("/{ai_model_id:uuid}")
    async def delete_ai_model(
        self,
        ai_models_service: AIModelsService,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to delete.",
        ),
    ) -> None:
        """Delete an AI model from the system."""
        from services.ai_services.router import refresh_router

        _ = await ai_models_service.delete(ai_model_id)
        clear_model_cache()
        await refresh_router()  # Refresh LiteLLM router after model deletion

    @post("/set_default", status_code=HTTP_204_NO_CONTENT)
    async def set_default_handler(
        self, ai_models_service: AIModelsService, data: AIModelSetDefaultRequest
    ) -> None:
        """Set default model handler."""
        try:
            await ai_models_service.set_default(data.type, data.system_name)
        except LookupError as e:
            logger.warning(str(e))
            raise NotFoundException(str(e))
        except Exception as err:
            logger.error(
                "Unexpected error occurred while setting default model: %s",
                err,
            )
            raise ClientException(
                "Unexpected error occurred while setting default model"
            )

    @post(
        "/{ai_model_id:uuid}/test",
        summary="Test model",
        status_code=HTTP_200_OK,
    )
    async def test_model(
        self,
        ai_models_service: AIModelsService,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to test.",
        ),
    ) -> ModelTestResult:
        """
        Test an AI model by making a simple API call.

        This endpoint verifies that the model configuration is correct
        by attempting to make a request to the model through its provider.
        For chat models, it sends a simple greeting.
        For embedding models, it generates embeddings for test text.
        """
        try:
            # Get the model from database
            model = await ai_models_service.get(ai_model_id)
            if not model:
                return ModelTestResult(
                    success=False,
                    message="Model not found",
                    error=f"Model with ID {ai_model_id} does not exist",
                )

            # Get the provider system name
            provider_system_name = model.provider_system_name
            if not provider_system_name:
                return ModelTestResult(
                    success=False,
                    message="Provider not configured",
                    error="Model does not have a provider_system_name configured",
                )

            # Try to get the AI provider instance
            try:
                # Import here to avoid circular import
                from services.ai_services.factory import get_ai_provider

                ai_provider = await get_ai_provider(provider_system_name)
            except ValueError as e:
                return ModelTestResult(
                    success=False,
                    message="Provider configuration error",
                    error=str(e),
                )

            model_type = model.type or "prompts"
            model_name = model.ai_model

            if model_type == "embeddings":
                # Test embedding model
                try:
                    response = await ai_provider.get_embeddings(
                        text="Test embedding generation",
                        llm=model_name,
                    )
                    if response and response.data:
                        vector_length = len(response.data)
                        return ModelTestResult(
                            success=True,
                            message=f"Embedding model '{model.display_name}' is working correctly!",
                            error=None,
                            response_preview=f"Generated embedding with {vector_length} dimensions",
                        )
                    else:
                        return ModelTestResult(
                            success=False,
                            message="Received empty embedding response",
                            error="No embedding data returned from provider",
                        )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support embeddings",
                        error="The configured provider does not implement the get_embeddings method",
                    )

            elif model_type == "re-ranking":
                # For re-ranking models, we can't easily test without documents
                # Just verify the provider is accessible
                return ModelTestResult(
                    success=True,
                    message=f"Re-ranking model '{model.display_name}' configuration verified. Full testing requires documents.",
                    error=None,
                    response_preview="Configuration validated (re-ranking requires documents for full test)",
                )

            else:
                # Test chat/prompt model
                test_messages = [
                    {"role": "user", "content": "Say 'OK' if you can hear me."}
                ]

                try:
                    response = await ai_provider.create_chat_completion(
                        messages=test_messages,
                        model=model_name,
                        temperature=0,
                        top_p=1,
                        max_tokens=10,  # Minimal tokens to save costs
                    )

                    if response and response.choices:
                        content = response.choices[0].message.content or ""
                        # Truncate long responses
                        preview = (
                            content[:100] + "..." if len(content) > 100 else content
                        )
                        return ModelTestResult(
                            success=True,
                            message=f"Model '{model.display_name}' is working correctly!",
                            error=None,
                            response_preview=preview,
                        )
                    else:
                        return ModelTestResult(
                            success=False,
                            message="Connection established but received unexpected response",
                            error="No response choices returned from model",
                        )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support chat completions",
                        error="The configured provider does not implement chat completions",
                    )

        except Exception as e:
            logger.exception("Error testing model %s", ai_model_id)
            return ModelTestResult(
                success=False,
                message="Model test failed",
                error=str(e),
            )

    @get(
        "/{ai_model_id:uuid}/capabilities",
        summary="Get model capabilities",
        status_code=HTTP_200_OK,
    )
    async def get_model_capabilities(
        self,
        ai_models_service: AIModelsService,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to get capabilities for.",
        ),
    ) -> ModelCapabilities:
        """
        Get model capabilities and supported parameters from LiteLLM.

        Returns information about what parameters the model supports,
        token limits, and special capabilities like vision or function calling.
        """
        import litellm

        model = await ai_models_service.get(ai_model_id)
        if not model:
            raise NotFoundException(f"Model with ID {ai_model_id} not found")

        model_name = model.ai_model

        # Get supported parameters
        try:
            supported_params = litellm.get_supported_openai_params(model_name) or []
        except Exception:
            supported_params = []

        # Get model info
        try:
            info = litellm.get_model_info(model_name)
        except Exception:
            info = {}

        return ModelCapabilities(
            supported_params=supported_params,
            max_tokens=info.get("max_tokens"),
            max_input_tokens=info.get("max_input_tokens"),
            max_output_tokens=info.get("max_output_tokens"),
            supports_vision=info.get("supports_vision", False),
            supports_function_calling=info.get("supports_function_calling", False),
            supports_response_schema=info.get("supports_response_schema", False),
            supports_audio_input=info.get("supports_audio_input", False),
            supports_audio_output=info.get("supports_audio_output", False),
            input_cost_per_token=info.get("input_cost_per_token"),
            output_cost_per_token=info.get("output_cost_per_token"),
        )
