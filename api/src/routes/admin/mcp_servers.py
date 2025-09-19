from typing import Any

from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from mcp import Tool
from mcp.types import CallToolResult

from services.mcp_servers import services


class McpServersController(Controller):
    path = "/mcp_servers"
    tags = ["mcp_servers"]

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

    @post(
        "/{id:str}/sync_tools",
        summary="Sync MCP server tools",
        status_code=HTTP_200_OK,
    )
    async def sync_mcp_server_tools(self, id: str) -> list[Tool]:
        return await services.sync_mcp_server_tools(id)

    @post(
        "/{id:str}/test",
        summary="Test MCP server connection",
        status_code=HTTP_200_OK,
    )
    async def test_mcp_server_connection(self, id: str) -> None:
        return await services.test_mcp_server_connection(id)
