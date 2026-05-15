from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Dict, List
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK
from mcp import Tool
from mcp.types import CallToolResult
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.mcp_servers.service import (
    MCPServersService,
)
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    visibility_filter_for,
)
from services.mcp_servers import services

from .schemas import MCPServerCreate, MCPServerResponse, MCPServerUpdate

if TYPE_CHECKING:
    pass


_RESOURCE = "mcp_servers"


class SecretsUpdateRequest(BaseModel):
    """Schema for partial secrets update."""

    secrets: Dict[str, Any] = Field(..., description="Secrets to update/add")


class SecretsDeleteRequest(BaseModel):
    """Schema for deleting specific secret keys."""

    keys: List[str] = Field(..., description="List of secret keys to delete")


class MCPServersController(Controller):
    """MCP servers CRUD — tenant + record-level scoped (PR 10 rollout)."""

    path = "/mcp_servers"
    tags = ["Admin / MCP Servers"]

    dependencies = providers.create_service_dependencies(
        MCPServersService,
        "mcp_servers_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.MCP_SERVERS_READ)])
    async def list_mcp_servers(
        self,
        mcp_servers_service: MCPServersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[MCPServerResponse]:
        """List MCP servers — filtered by record-level visibility."""
        from core.db.models.mcp_server.mcp_server import MCPServer as MCPServerModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            mcp_servers_service,
            request=request,
            model=MCPServerModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await mcp_servers_service.list_and_count(*extra_filters)
        page = mcp_servers_service.to_schema(
            results, total, filters=filters, schema_type=MCPServerResponse
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    mcp_servers_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.MCP_SERVERS_WRITE)])
    async def create_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        data: MCPServerCreate,
        request: Request,
        audit_username: str | None,
    ) -> MCPServerResponse:
        """Create a new MCP server. tenant_id + owner_id forced from auth."""
        from core.db.models.mcp_server.mcp_server import MCPServer as MCPServerModel

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await mcp_servers_service.create(
            MCPServerModel(**payload), auto_commit=True
        )
        schema = mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)
        return await attach_permissions(
            mcp_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/code/{code:str}",
        guards=[require_permission(Permission.MCP_SERVERS_READ)],
    )
    async def get_mcp_server_by_code(
        self, mcp_servers_service: MCPServersService, code: str, request: Request
    ) -> MCPServerResponse:
        """Get an MCP server by its system_name."""
        obj = await mcp_servers_service.get_one(system_name=code)
        await enforce_view_or_404(
            mcp_servers_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)
        return await attach_permissions(
            mcp_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/{mcp_server_id:uuid}",
        guards=[require_permission(Permission.MCP_SERVERS_READ)],
    )
    async def get_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        request: Request,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to retrieve.",
        ),
    ) -> MCPServerResponse:
        """Get an MCP server by its ID. 404 if caller can't view it."""
        obj = await mcp_servers_service.get(mcp_server_id)
        await enforce_view_or_404(
            mcp_servers_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)
        return await attach_permissions(
            mcp_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @patch(
        "/{mcp_server_id:uuid}",
        guards=[require_permission(Permission.MCP_SERVERS_WRITE)],
    )
    async def update_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        data: MCPServerUpdate,
        request: Request,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to update.",
        ),
        audit_username: str | None = None,
    ) -> MCPServerResponse:
        """Update an MCP server. 404/403 per record-level access rules."""
        existing = await mcp_servers_service.get(mcp_server_id)
        await enforce_action_or_403(
            mcp_servers_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await mcp_servers_service.update(
            update_data, item_id=mcp_server_id, auto_commit=True
        )
        schema = mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)
        return await attach_permissions(
            mcp_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @delete(
        "/{mcp_server_id:uuid}",
        guards=[require_permission(Permission.MCP_SERVERS_DELETE)],
    )
    async def delete_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        request: Request,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to delete.",
        ),
    ) -> None:
        """Delete an MCP server. 404/403 per record-level access rules."""
        existing = await mcp_servers_service.get(mcp_server_id)
        await enforce_action_or_403(
            mcp_servers_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        _ = await mcp_servers_service.delete(mcp_server_id)

    @post(
        "/{mcp_server_id:uuid}/tools/{tool:str}/call",
        summary="Call MCP server tool",
        status_code=HTTP_200_OK,
    )
    async def call_mcp_server_tool(
        self, mcp_server_id: UUID, tool: str, data: dict[str, Any]
    ) -> CallToolResult:
        """Call a tool on the MCP server."""
        return await services.call_mcp_server_tool(
            mcp_server_id=str(mcp_server_id), tool=tool, arguments=data
        )

    @post(
        "/{mcp_server_id:uuid}/sync_tools",
        summary="Sync MCP server tools",
        status_code=HTTP_200_OK,
    )
    async def sync_mcp_server_tools(self, mcp_server_id: UUID) -> list[Tool]:
        """Sync tools from the MCP server."""
        return await services.sync_mcp_server_tools(str(mcp_server_id))

    @post(
        "/{mcp_server_id:uuid}/test",
        summary="Test MCP server connection",
        status_code=HTTP_200_OK,
    )
    async def test_mcp_server_connection(self, mcp_server_id: UUID) -> None:
        """Test connection to the MCP server."""
        return await services.test_mcp_server_connection(str(mcp_server_id))
