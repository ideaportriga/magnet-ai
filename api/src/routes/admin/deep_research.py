"""Deep Research API routes - using database services."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import HTTPException
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.deep_research.schemas import (
    DeepResearchConfigCreateSchema,
    DeepResearchConfigSchema,
    DeepResearchConfigUpdateSchema,
    DeepResearchRunCreateRequestSchema,
    DeepResearchRunCreateSchema,
    DeepResearchRunCreatedResponse,
    DeepResearchRunSchema,
)
from core.domain.deep_research.service import (
    DeepResearchConfigService,
    DeepResearchRunService,
)
from services.deep_research.models import DeepResearchConfig
from services.deep_research.services import run_deep_research_workflow

if TYPE_CHECKING:
    pass


class DeepResearchConfigController(Controller):
    """Deep Research Config CRUD"""

    path = "/deep-research/configs"
    tags = ["Admin / Deep Research"]

    dependencies = providers.create_service_dependencies(
        DeepResearchConfigService,
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
        config_service: DeepResearchConfigService,
        data: Annotated[DeepResearchConfigCreateSchema, Body()],
    ) -> DeepResearchConfigSchema:
        """Create a new deep research config."""
        obj = await config_service.create(data)
        return config_service.to_schema(obj, schema_type=DeepResearchConfigSchema)

    @get()
    async def list_configs(
        self,
        config_service: DeepResearchConfigService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[DeepResearchConfigSchema]:
        """List deep research configs with pagination and filtering."""
        results, total = await config_service.list_and_count(*filters)
        return config_service.to_schema(
            results, total, filters=filters, schema_type=DeepResearchConfigSchema
        )

    @get("/{config_id:uuid}")
    async def get_config(
        self,
        config_service: DeepResearchConfigService,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to retrieve.",
        ),
    ) -> DeepResearchConfigSchema:
        """Get a deep research config by its ID."""
        obj = await config_service.get(config_id)
        return config_service.to_schema(obj, schema_type=DeepResearchConfigSchema)

    @patch("/{config_id:uuid}")
    async def update_config(
        self,
        config_service: DeepResearchConfigService,
        data: DeepResearchConfigUpdateSchema,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to update.",
        ),
    ) -> DeepResearchConfigSchema:
        """Update a deep research config."""
        obj = await config_service.update(data, item_id=config_id, auto_commit=True)
        return config_service.to_schema(obj, schema_type=DeepResearchConfigSchema)

    @delete("/{config_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_config(
        self,
        config_service: DeepResearchConfigService,
        config_id: UUID = Parameter(
            title="Config ID",
            description="The config to delete.",
        ),
    ) -> None:
        """Delete a deep research config."""
        _ = await config_service.delete(config_id)


class DeepResearchRunController(Controller):
    """Deep Research Run CRUD"""

    path = "/deep-research/runs"
    tags = ["Admin / Deep Research"]

    dependencies = {
        **providers.create_service_dependencies(
            DeepResearchRunService,
            "run_service",
            filters={
                "pagination_type": "limit_offset",
                "id_filter": UUID,
                "pagination_size": DEFAULT_PAGINATION_SIZE,
                "sort_field": "updated_at",
                "sort_order": "desc",
            },
        ),
        **providers.create_service_dependencies(
            DeepResearchConfigService,
            "config_service",
        ),
    }

    @post(status_code=HTTP_201_CREATED)
    async def create_run(
        self,
        run_service: DeepResearchRunService,
        config_service: DeepResearchConfigService,
        data: Annotated[DeepResearchRunCreateRequestSchema, Body()],
    ) -> DeepResearchRunCreatedResponse:
        """Create a new deep research run and trigger execution asynchronously."""

        if data.input is None:
            raise HTTPException(status_code=400, detail="'input' is required")

        # Determine configuration snapshot
        config_payload = data.config
        config_system_name = data.config_system_name
        if data.config_system_name:
            config_obj = await config_service.get_one(
                system_name=data.config_system_name
            )
            config_payload = config_obj.config
            config_system_name = config_obj.system_name

        # Validate and enrich configuration with defaults
        config_model = DeepResearchConfig.model_validate(config_payload or {})
        config_snapshot = config_model.model_dump()

        run_data = DeepResearchRunCreateSchema(
            client_id=data.client_id,
            input=data.input,
            config=config_snapshot,
            config_system_name=config_system_name,
        )

        obj = await run_service.create(run_data, auto_commit=True)

        run_id = str(obj.id)
        asyncio.create_task(run_deep_research_workflow(run_id))

        return DeepResearchRunCreatedResponse(run_id=obj.id)

    @get()
    async def list_runs(
        self,
        run_service: DeepResearchRunService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[DeepResearchRunSchema]:
        """List deep research runs with pagination and filtering."""
        results, total = await run_service.list_and_count(*filters)
        return run_service.to_schema(
            results, total, filters=filters, schema_type=DeepResearchRunSchema
        )

    @get("/{run_id:uuid}")
    async def get_run(
        self,
        run_service: DeepResearchRunService,
        run_id: UUID = Parameter(
            title="Run ID",
            description="The run to retrieve.",
        ),
    ) -> DeepResearchRunSchema:
        """Get a deep research run by its ID."""
        obj = await run_service.get(run_id)
        return run_service.to_schema(obj, schema_type=DeepResearchRunSchema)

    @get("/client-id/{client_id:str}")
    async def get_run_by_client_id(
        self,
        run_service: DeepResearchRunService,
        client_id: str = Parameter(
            title="Client ID",
            description="The client_id of the run to retrieve.",
        ),
    ) -> DeepResearchRunSchema:
        """Get a deep research run by its client_id. Returns the first match if multiple exist."""
        # Use list with limit=1 instead of get_one to handle multiple matches
        results = await run_service.list(client_id=client_id)
        if not results:
            from litestar.exceptions import NotFoundException

            raise NotFoundException(detail=f"No run found with client_id: {client_id}")

        # Return the first result
        obj = results[0]
        return run_service.to_schema(obj, schema_type=DeepResearchRunSchema)

    @delete("/{run_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_run(
        self,
        run_service: DeepResearchRunService,
        run_id: UUID = Parameter(
            title="Run ID",
            description="The run to delete.",
        ),
    ) -> None:
        """Delete a deep research run."""
        _ = await run_service.delete(run_id)

    @delete("/client-id/{client_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def delete_run_by_client_id(
        self,
        run_service: DeepResearchRunService,
        client_id: str = Parameter(
            title="Client ID",
            description="The client_id of the run to delete.",
        ),
    ) -> None:
        """Delete a deep research run by its client_id. Deletes the first match if multiple exist."""
        # Use list with limit=1 instead of get_one to handle multiple matches
        results = await run_service.list(client_id=client_id)
        if not results:
            from litestar.exceptions import NotFoundException

            raise NotFoundException(detail=f"No run found with client_id: {client_id}")

        # Delete the first result
        obj = results[0]
        _ = await run_service.delete(obj.id)
