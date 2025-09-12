from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.api_tools.service import (
    ApiToolsService,
)

from .schemas import ApiTool, ApiToolCreate, ApiToolUpdate

if TYPE_CHECKING:
    pass


class ApiToolsController(Controller):
    """API Tools CRUD"""

    path = "/sql_api_tools"
    tags = ["sql_ApiTools"]

    dependencies = providers.create_service_dependencies(
        ApiToolsService,
        "api_tools_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_api_tools(
        self,
        api_tools_service: ApiToolsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[ApiTool]:
        """List API tools with pagination and filtering."""
        results, total = await api_tools_service.list_and_count(*filters)
        return api_tools_service.to_schema(
            results, total, filters=filters, schema_type=ApiTool
        )

    @post()
    async def create_api_tool(
        self, api_tools_service: ApiToolsService, data: ApiToolCreate
    ) -> ApiTool:
        """Create a new API tool."""
        obj = await api_tools_service.create(data)
        return api_tools_service.to_schema(obj, schema_type=ApiTool)

    @post("/bulk")
    async def create_api_tools_bulk(
        self, api_tools_service: ApiToolsService, data: list[ApiToolCreate]
    ) -> list[ApiTool]:
        """Create multiple API tools in bulk."""
        objs = await api_tools_service.create_many(data)
        return [api_tools_service.to_schema(obj, schema_type=ApiTool) for obj in objs]

    @get("/code/{code:str}")
    async def get_api_tool_by_code(
        self, api_tools_service: ApiToolsService, code: str
    ) -> ApiTool:
        """Get an API tool by its system_name."""
        obj = await api_tools_service.get_one(system_name=code)
        return api_tools_service.to_schema(obj, schema_type=ApiTool)

    @get("/{api_tool_id:uuid}")
    async def get_api_tool(
        self,
        api_tools_service: ApiToolsService,
        api_tool_id: UUID = Parameter(
            title="API Tool ID",
            description="The API tool to retrieve.",
        ),
    ) -> ApiTool:
        """Get an API tool by its ID."""
        obj = await api_tools_service.get(api_tool_id)
        return api_tools_service.to_schema(obj, schema_type=ApiTool)

    @patch("/{api_tool_id:uuid}")
    async def update_api_tool(
        self,
        api_tools_service: ApiToolsService,
        data: ApiToolUpdate,
        api_tool_id: UUID = Parameter(
            title="API Tool ID",
            description="The API tool to update.",
        ),
    ) -> ApiTool:
        """Update an API tool."""
        obj = await api_tools_service.update(data, item_id=api_tool_id, auto_commit=True)
        return api_tools_service.to_schema(obj, schema_type=ApiTool)

    @patch("/bulk")
    async def update_api_tools_bulk(
        self, api_tools_service: ApiToolsService, data: list[ApiToolUpdate]
    ) -> list[ApiTool]:
        """Update multiple API tools in bulk."""
        objs = await api_tools_service.update_many(data)
        return [api_tools_service.to_schema(obj, schema_type=ApiTool) for obj in objs]

    @delete("/{api_tool_id:uuid}")
    async def delete_api_tool(
        self,
        api_tools_service: ApiToolsService,
        api_tool_id: UUID = Parameter(
            title="API Tool ID",
            description="The API tool to delete.",
        ),
    ) -> None:
        """Delete an API tool from the system."""
        _ = await api_tools_service.delete(api_tool_id)

    @delete("/bulk")
    async def delete_api_tools_bulk(
        self, api_tools_service: ApiToolsService, data: list[UUID]
    ) -> None:
        """Delete multiple API tools in bulk."""
        await api_tools_service.delete_many(data)
