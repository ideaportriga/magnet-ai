from typing import Any

from litestar import Controller, delete, get, post, put
from litestar.status_codes import HTTP_200_OK
from mcp.types import CallToolResult, Tool

from services.mcp_servers import services
from services.mcp_servers.types import (
    McpServerConfigEntity,
    McpServerConfigPersisted,
    McpServerConfigWithSecrets,
    McpServerUpdate,
)


class McpServersController(Controller):
    path = "/mcp_servers"
    tags = ["mcp_servers"]

    @get("/", summary="List MCP servers")
    async def list_mcp_servers(self) -> list[McpServerConfigEntity]:
        return await services.list_mcp_servers()

    @get("/{id:str}", summary="Get MCP server")
    async def get_mcp_server(self, id: str) -> McpServerConfigEntity:
        return await services.get_mcp_server(id)

    @post("/", summary="Create MCP server", response_model=McpServerConfigPersisted)
    async def create_mcp_server(self, data: McpServerConfigWithSecrets) -> dict:
        return await services.create_mcp_server(data)

    @put("/{id:str}", summary="Update MCP server")
    async def update_mcp_server(self, id: str, data: McpServerUpdate) -> dict:
        await services.update_mcp_server(id, data)
        return {}

    @post(
        "/{id:str}/test",
        summary="Test MCP server connection",
        status_code=HTTP_200_OK,
    )
    async def test_mcp_server_connection(self, id: str) -> None:
        return await services.test_mcp_server_connection(id)

    @post(
        "/{id:str}/sync_tools",
        summary="Sync MCP server tools",
        status_code=HTTP_200_OK,
    )
    async def sync_mcp_server_tools(self, id: str) -> list[Tool]:
        return await services.sync_mcp_server_tools(id)

    @post(
        "/{mcp_server_id:str}/tools/{tool:str}/call",
        summary="Call MCP server tool",
        status_code=HTTP_200_OK,
    )
    async def call_mcp_server_tool(
        self, mcp_server_id: str, tool: str, data: dict[str, Any]
    ) -> CallToolResult:
        return await services.call_mcp_server_tool(
            mcp_server_id=mcp_server_id, tool=tool, arguments=data
        )

    @delete("/{id:str}", summary="Delete MCP server")
    async def delete_mcp_server(self, id: str) -> None:
        return await services.delete_mcp_server(id)
