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
from core.domain.providers.service import ProvidersService
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
    # LiteLLM diagnostic info
    litellm_model_string: str | None = Field(
        None, description="Full LiteLLM model string used (e.g. 'openai/gpt-4o')"
    )
    effective_endpoint: str | None = Field(
        None, description="Provider endpoint that will be used for API calls"
    )
    via_router: bool | None = Field(
        None, description="Whether the model routes through the global LiteLLM Router"
    )
    computed_url: str | None = Field(
        None, description="Approximate full URL that LiteLLM will send requests to"
    )
    response_audio_base64: str | None = Field(
        None, description="Base64-encoded audio for TTS test playback"
    )
    response_audio_format: str | None = Field(
        None, description="Audio format for TTS test (e.g. 'mp3', 'wav')"
    )


class ModelDebugInfo(BaseModel):
    """LiteLLM routing diagnostic information for a model (no API call made)."""

    model_system_name: str = Field(..., description="Model system_name")
    model_ai_model: str = Field(..., description="Model identifier (e.g. 'gpt-4o')")
    provider_system_name: str | None = Field(None, description="Provider system_name")
    litellm_model_string: str | None = Field(
        None, description="Full LiteLLM model string (e.g. 'azure/gpt-4o')"
    )
    effective_endpoint: str | None = Field(
        None, description="Endpoint that will be used for API calls"
    )
    via_router: bool = Field(
        ..., description="Whether the model is registered in the global LiteLLM Router"
    )
    computed_url: str | None = Field(
        None, description="Approximate full URL that LiteLLM will send requests to"
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

    dependencies = {
        **providers.create_service_dependencies(
            AIModelsService,
            "ai_models_service",
            filters={
                "pagination_type": "limit_offset",
                "id_filter": UUID,
                "search": "name",
                "search_ignore_case": True,
                "pagination_size": DEFAULT_PAGINATION_SIZE,
                "sort_field": "updated_at",
                "sort_order": "desc",
            },
        ),
        **providers.create_service_dependencies(
            ProvidersService,
            "providers_service",
        ),
    }

    @get()
    async def list_ai_models(
        self,
        ai_models_service: AIModelsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        type: Annotated[str | None, Parameter(query="type", required=False)] = None,
        provider: Annotated[
            str | None, Parameter(query="provider", required=False)
        ] = None,
    ) -> service.OffsetPagination[AIModel]:
        """List AI models with pagination and filtering."""
        from advanced_alchemy.filters import CollectionFilter

        active_filters = list(filters)
        if type is not None:
            active_filters.append(CollectionFilter(field_name="type", values=[type]))
        if provider is not None:
            active_filters.append(
                CollectionFilter(field_name="provider_system_name", values=[provider])
            )
        results, total = await ai_models_service.list_and_count(*active_filters)
        return ai_models_service.to_schema(
            results, total, filters=active_filters, schema_type=AIModel
        )

    @post()
    async def create_ai_model(
        self,
        ai_models_service: AIModelsService,
        data: AIModelCreate,
        audit_username: str | None,
    ) -> AIModel:
        """Create a new AI model."""
        from services.ai_services.router import refresh_router

        data.created_by = audit_username
        data.updated_by = audit_username
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
        audit_username: str | None = None,
    ) -> AIModel:
        """Update an AI model."""
        from services.ai_services.router import refresh_router

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = audit_username
        obj = await ai_models_service.update(
            update_data, item_id=ai_model_id, auto_commit=True
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
        providers_service: ProvidersService,
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

        The response includes LiteLLM diagnostic info:
        - litellm_model_string: full model string passed to LiteLLM
        - effective_endpoint: the endpoint used for API calls
        - via_router: whether the request goes through the global LiteLLM Router
        - computed_url: approximate full URL LiteLLM will call
        """
        debug_info: dict = {
            "litellm_model_string": None,
            "effective_endpoint": None,
            "via_router": None,
            "computed_url": None,
        }
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

            # Ensure router is initialized before checking is_model_in_router()
            from services.ai_services.router import get_router

            await get_router()

            # Compute diagnostic info (read-only, no API call)
            from services.ai_services.utils import get_litellm_debug_info

            provider = await providers_service.get_one_or_none(
                system_name=provider_system_name
            )
            if provider:
                debug_info = get_litellm_debug_info(
                    provider_data={
                        "type": provider.type,
                        "endpoint": provider.endpoint,
                        "connection_config": provider.connection_config or {},
                    },
                    model_name=model.ai_model,
                    model_system_name=model.system_name,
                    model_routing_config=model.routing_config,
                    model_type=model.type,
                )
            else:
                debug_info = {
                    "litellm_model_string": None,
                    "effective_endpoint": None,
                    "via_router": None,
                    "computed_url": None,
                }

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
                    **debug_info,
                )

            model_type = model.type or "prompts"
            model_name = model.ai_model
            rc = model.routing_config
            routing_config_dict = (
                rc
                if isinstance(rc, dict)
                else rc.model_dump(exclude_none=True)
                if rc
                else {}
            )
            model_config = {
                "system_name": model.system_name,
                "routing_config": routing_config_dict,
            }

            if model_type == "embeddings":
                # Test embedding model
                try:
                    response = await ai_provider.get_embeddings(
                        text="Test embedding generation",
                        llm=model_name,
                        model_config=model_config,
                    )
                    if response and response.data:
                        vector_length = len(response.data)
                        return ModelTestResult(
                            success=True,
                            message=f"Embedding model '{model.display_name}' is working correctly!",
                            error=None,
                            response_preview=f"Generated embedding with {vector_length} dimensions",
                            **debug_info,
                        )
                    else:
                        return ModelTestResult(
                            success=False,
                            message="Received empty embedding response",
                            error="No embedding data returned from provider",
                            **debug_info,
                        )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support embeddings",
                        error="The configured provider does not implement the get_embeddings method",
                        **debug_info,
                    )
                except Exception as e:
                    return ModelTestResult(
                        success=False,
                        message="Embedding test failed",
                        error=str(e),
                        **debug_info,
                    )

            elif model_type == "re-ranking":
                # Test rerank model with minimal synthetic documents
                from decimal import Decimal

                from models import DocumentSearchResultItem

                test_docs = [
                    DocumentSearchResultItem(
                        id="test-1",
                        content="Python is a programming language.",
                        metadata={},
                        score=Decimal("0.5"),
                        collection_id="test",
                    ),
                    DocumentSearchResultItem(
                        id="test-2",
                        content="The weather is sunny today.",
                        metadata={},
                        score=Decimal("0.5"),
                        collection_id="test",
                    ),
                ]
                try:
                    response = await ai_provider.rerank(
                        query="programming language",
                        documents=test_docs,
                        llm=model_name,
                        top_n=2,
                        truncation=False,
                        model_config=model_config,
                    )
                    return ModelTestResult(
                        success=True,
                        message=f"Re-ranking model '{model.display_name}' is working correctly!",
                        error=None,
                        response_preview=f"Reranked {len(response.data)} documents",
                        **debug_info,
                    )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support reranking",
                        error="The configured provider does not implement the rerank method",
                        **debug_info,
                    )
                except Exception as e:
                    return ModelTestResult(
                        success=False,
                        message="Re-ranking test failed",
                        error=str(e),
                        **debug_info,
                    )

            elif model_type == "stt":
                # Test speech-to-text model with a WAV containing a 440 Hz tone
                import io
                import math
                import struct

                def _make_tone_wav(
                    duration_sec: int = 2, sample_rate: int = 16000, freq: float = 440.0
                ) -> io.BytesIO:
                    num_samples = sample_rate * duration_sec
                    samples = [
                        int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
                        for i in range(num_samples)
                    ]
                    data = struct.pack(f"<{num_samples}h", *samples)
                    data_size = len(data)
                    buf = io.BytesIO()
                    buf.write(b"RIFF")
                    buf.write(struct.pack("<I", 36 + data_size))
                    buf.write(b"WAVE")
                    buf.write(b"fmt ")
                    buf.write(struct.pack("<I", 16))
                    buf.write(struct.pack("<H", 1))  # PCM
                    buf.write(struct.pack("<H", 1))  # mono
                    buf.write(struct.pack("<I", sample_rate))
                    buf.write(struct.pack("<I", sample_rate * 2))
                    buf.write(struct.pack("<H", 2))
                    buf.write(struct.pack("<H", 16))
                    buf.write(b"data")
                    buf.write(struct.pack("<I", data_size))
                    buf.write(data)
                    buf.seek(0)
                    buf.name = "test.wav"
                    return buf

                try:
                    test_audio = _make_tone_wav()
                    logger.warning(
                        "[stt-test] provider_class=%s model=%s",
                        type(ai_provider).__name__,
                        model_name,
                    )
                    response = await ai_provider.transcribe(
                        file=test_audio,
                        model=model_name,
                        model_config=model_config,
                    )
                    preview = (
                        f'Transcription: "{response.text}"'
                        if response.text
                        else "Transcription returned empty text (silent audio)"
                    )
                    if response.duration is not None:
                        preview += f" | Duration: {response.duration:.1f}s"
                    return ModelTestResult(
                        success=True,
                        message=f"STT model '{model.display_name}' is working correctly!",
                        error=None,
                        response_preview=preview,
                        **debug_info,
                    )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support speech-to-text",
                        error="The configured provider does not implement the transcribe method",
                        **debug_info,
                    )
                except Exception as e:
                    return ModelTestResult(
                        success=False,
                        message="STT test failed",
                        error=str(e),
                        **debug_info,
                    )

            elif model_type == "tts":
                # Test text-to-speech model
                import base64

                test_text = "Hello! This is a test of the text to speech model."
                try:
                    audio_bytes = await ai_provider.speech(
                        input=test_text,
                        model=model_name,
                    )
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    size_kb = len(audio_bytes) / 1024
                    return ModelTestResult(
                        success=True,
                        message=f"TTS model '{model.display_name}' is working correctly!",
                        error=None,
                        response_preview=f"Generated {size_kb:.1f} KB of audio",
                        response_audio_base64=audio_b64,
                        response_audio_format="mp3",
                        **debug_info,
                    )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support text-to-speech",
                        error="The configured provider does not implement the speech method",
                        **debug_info,
                    )
                except Exception as e:
                    return ModelTestResult(
                        success=False,
                        message="TTS test failed",
                        error=str(e),
                        **debug_info,
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
                        max_tokens=16,  # Minimal tokens to save costs (Responses API requires >= 16)
                        model_config=model_config,
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
                            **debug_info,
                        )
                    else:
                        return ModelTestResult(
                            success=False,
                            message="Connection established but received unexpected response",
                            error="No response choices returned from model",
                            **debug_info,
                        )
                except NotImplementedError:
                    return ModelTestResult(
                        success=False,
                        message="Provider does not support chat completions",
                        error="The configured provider does not implement chat completions",
                        **debug_info,
                    )
                except Exception as e:
                    return ModelTestResult(
                        success=False,
                        message="Chat completion test failed",
                        error=str(e),
                        **debug_info,
                    )

        except Exception as e:
            logger.exception("Error testing model %s", ai_model_id)
            return ModelTestResult(
                success=False,
                message="Model test failed",
                error=str(e),
                **debug_info,
            )

    @get(
        "/{ai_model_id:uuid}/debug-info",
        summary="Get LiteLLM routing debug info",
        status_code=HTTP_200_OK,
    )
    async def get_model_debug_info(
        self,
        ai_models_service: AIModelsService,
        providers_service: ProvidersService,
        ai_model_id: UUID = Parameter(
            title="AI Model ID",
            description="The AI model to get debug info for.",
        ),
    ) -> ModelDebugInfo:
        """
        Get LiteLLM routing diagnostic information for a model without making an API call.

        Returns:
        - litellm_model_string: full model string passed to LiteLLM (e.g. 'azure/gpt-4o')
        - effective_endpoint: endpoint used for API calls (provider-level or model-level override)
        - via_router: whether the model is registered in the global LiteLLM Router
        - computed_url: approximate full URL that LiteLLM will call
        """
        from services.ai_services.router import get_router
        from services.ai_services.utils import get_litellm_debug_info

        await get_router()

        model = await ai_models_service.get(ai_model_id)
        if not model:
            raise NotFoundException(f"Model with ID {ai_model_id} not found")

        provider = None
        if model.provider_system_name:
            provider = await providers_service.get_one_or_none(
                system_name=model.provider_system_name
            )

        if provider:
            debug_info = get_litellm_debug_info(
                provider_data={
                    "type": provider.type,
                    "endpoint": provider.endpoint,
                    "connection_config": provider.connection_config or {},
                },
                model_name=model.ai_model,
                model_system_name=model.system_name,
                model_routing_config=model.routing_config,
                model_type=model.type,
            )
        else:
            from services.ai_services.router import is_model_in_router

            debug_info = {
                "litellm_model_string": None,
                "effective_endpoint": None,
                "via_router": is_model_in_router(model.system_name),
                "computed_url": None,
            }

        return ModelDebugInfo(
            model_system_name=model.system_name,
            model_ai_model=model.ai_model,
            provider_system_name=model.provider_system_name,
            **debug_info,
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
            supports_vision=bool(info.get("supports_vision") or False),
            supports_function_calling=bool(
                info.get("supports_function_calling") or False
            ),
            supports_response_schema=bool(
                info.get("supports_response_schema") or False
            ),
            supports_audio_input=bool(info.get("supports_audio_input") or False),
            supports_audio_output=bool(info.get("supports_audio_output") or False),
            input_cost_per_token=info.get("input_cost_per_token"),
            output_cost_per_token=info.get("output_cost_per_token"),
        )
