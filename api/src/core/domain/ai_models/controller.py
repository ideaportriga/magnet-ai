from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_204_NO_CONTENT

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.ai_models.service import (
    AIModelsService,
)

from .schemas import AIModel, AIModelCreate, AIModelSetDefaultRequest, AIModelUpdate

if TYPE_CHECKING:
    pass

logger = getLogger(__name__)


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
        obj = await ai_models_service.create(data)
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
        obj = await ai_models_service.update(
            data, item_id=ai_model_id, auto_commit=True
        )
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
        _ = await ai_models_service.delete(ai_model_id)

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
