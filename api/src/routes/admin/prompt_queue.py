"""Prompt Queue API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.prompt_queue.schemas import (
    PromptQueueConfigCreateSchema,
    PromptQueueConfigSchema,
    PromptQueueConfigUpdateSchema,
    PromptQueueExecuteRequestSchema,
    PromptQueueExecuteResponseSchema,
)
from core.domain.prompt_queue.service import PromptQueueConfigService
from services.prompt_queue import execute_prompt_queue


class PromptQueueConfigController(Controller):
    """Prompt Queue Config CRUD."""

    path = "/prompt-queue/configs"
    tags = ["Admin / Prompt Queue"]

    dependencies = providers.create_service_dependencies(
        PromptQueueConfigService,
        "config_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @post(status_code=HTTP_201_CREATED)
    async def create_config(
        self,
        config_service: PromptQueueConfigService,
        data: Annotated[PromptQueueConfigCreateSchema, Body()],
        audit_username: str | None = None,
    ) -> PromptQueueConfigSchema:
        """Create a new prompt queue config."""
        data.created_by = audit_username
        data.updated_by = audit_username
        obj = await config_service.create(data)
        return config_service.to_schema(obj, schema_type=PromptQueueConfigSchema)

    @get()
    async def list_configs(
        self,
        config_service: PromptQueueConfigService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[PromptQueueConfigSchema]:
        """List prompt queue configs with pagination and filtering."""
        results, total = await config_service.list_and_count(*filters)
        return config_service.to_schema(
            results, total, filters=filters, schema_type=PromptQueueConfigSchema
        )

    @get("/{config_id:uuid}")
    async def get_config(
        self,
        config_service: PromptQueueConfigService,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to retrieve.",
        ),
    ) -> PromptQueueConfigSchema:
        """Get a prompt queue config by its ID."""
        obj = await config_service.get(config_id)
        return config_service.to_schema(obj, schema_type=PromptQueueConfigSchema)

    @post("/{config_id:uuid}/execute", status_code=HTTP_200_OK)
    async def execute_config(
        self,
        config_service: PromptQueueConfigService,
        data: Annotated[PromptQueueExecuteRequestSchema, Body()],
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to execute.",
        ),
    ) -> PromptQueueExecuteResponseSchema:
        """Execute a prompt queue config with the given input."""
        obj = await config_service.get(config_id)
        config_dict = obj.config or {}
        result = await execute_prompt_queue(
            config=config_dict,
            input_data=data.input,
        )
        return PromptQueueExecuteResponseSchema(result=result)

    @patch("/{config_id:uuid}")
    async def update_config(
        self,
        config_service: PromptQueueConfigService,
        data: PromptQueueConfigUpdateSchema,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to update.",
        ),
        audit_username: str | None = None,
    ) -> PromptQueueConfigSchema:
        """Update a prompt queue config."""
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = audit_username
        obj = await config_service.update(
            update_data, item_id=config_id, auto_commit=True
        )
        return config_service.to_schema(obj, schema_type=PromptQueueConfigSchema)

    @delete("/{config_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_config(
        self,
        config_service: PromptQueueConfigService,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to delete.",
        ),
    ) -> None:
        """Delete a prompt queue config."""
        _ = await config_service.delete(config_id)
