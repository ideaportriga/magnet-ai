from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Dict, List
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.mcp_servers.service import (
    MCPServersService,
)

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

    path = "/sql_mcp_servers"
    tags = ["sql_MCPServers"]

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
