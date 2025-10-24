from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Dict, List
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK
from mcp import Tool
from mcp.types import CallToolResult
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.mcp_servers.service import (
    MCPServersService,
)
from services.mcp_servers import services

from .schemas import MCPServerCreate, MCPServerResponse, MCPServerUpdate

if TYPE_CHECKING:
    pass


class SecretsUpdateRequest(BaseModel):
    """Schema for partial secrets update."""

    secrets: Dict[str, Any] = Field(..., description="Secrets to update/add")


class SecretsDeleteRequest(BaseModel):
    """Schema for deleting specific secret keys."""

    keys: List[str] = Field(..., description="List of secret keys to delete")


class MCPServersController(Controller):
    """MCP servers CRUD"""

    path = "/mcp_servers"
    tags = ["mcp_servers"]

    dependencies = providers.create_service_dependencies(
        MCPServersService,
        "mcp_servers_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_mcp_servers(
        self,
        mcp_servers_service: MCPServersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[MCPServerResponse]:
        """List MCP servers with pagination and filtering."""
        results, total = await mcp_servers_service.list_and_count(*filters)
        return mcp_servers_service.to_schema(
            results, total, filters=filters, schema_type=MCPServerResponse
        )

    @post()
    async def create_mcp_server(
        self, mcp_servers_service: MCPServersService, data: MCPServerCreate
    ) -> MCPServerResponse:
        """Create a new MCP server."""
        obj = await mcp_servers_service.create(data)
        return mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)

    @get("/code/{code:str}")
    async def get_mcp_server_by_code(
        self, mcp_servers_service: MCPServersService, code: str
    ) -> MCPServerResponse:
        """Get an MCP server by its system_name."""
        obj = await mcp_servers_service.get_one(system_name=code)
        return mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)

    @get("/{mcp_server_id:uuid}")
    async def get_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to retrieve.",
        ),
    ) -> MCPServerResponse:
        """Get an MCP server by its ID."""
        obj = await mcp_servers_service.get(mcp_server_id)
        return mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)

    @patch("/{mcp_server_id:uuid}")
    async def update_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        data: MCPServerUpdate,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to update.",
        ),
    ) -> MCPServerResponse:
        """Update an MCP server."""
        obj = await mcp_servers_service.update(
            data, item_id=mcp_server_id, auto_commit=True
        )
        return mcp_servers_service.to_schema(obj, schema_type=MCPServerResponse)

    @delete("/{mcp_server_id:uuid}")
    async def delete_mcp_server(
        self,
        mcp_servers_service: MCPServersService,
        mcp_server_id: UUID = Parameter(
            title="MCP Server ID",
            description="The MCP server to delete.",
        ),
    ) -> None:
        """Delete an MCP server from the system."""
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
