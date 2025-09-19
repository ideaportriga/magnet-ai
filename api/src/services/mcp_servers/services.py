from logging import getLogger

from mcp.types import CallToolResult, Tool

from core.config.app import alchemy
from core.domain.mcp_servers.schemas import MCPServerUpdate
from core.domain.mcp_servers.service import MCPServersService
from utils.secrets import replace_placeholders_in_dict

from .remote_client import init_client_session
from .types import (
    McpServerConfigWithSecrets,
    McpServerSessionParams,
    McpTransportProtocol,
)

logger = getLogger(__name__)


def get_mcp_server_session_params(
    mcp_server: McpServerConfigWithSecrets,
) -> McpServerSessionParams:
    """For internal use only. Do not expose secrets in API."""

    params = McpServerSessionParams(
        transport=mcp_server.transport,
        url=mcp_server.url,
        headers=mcp_server.headers,
    )

    if params.headers and mcp_server.secrets:
        params.headers = replace_placeholders_in_dict(
            params.headers, mcp_server.secrets
        )

    return params


async def get_mcp_server_with_secrets(
    id: str | None = None,
    system_name: str | None = None,
) -> McpServerConfigWithSecrets:
    """Get MCP server with secrets by id or system_name."""
    async with alchemy.get_session() as session:
        mcp_servers_service = MCPServersService(session=session)

        # Get MCP server with secrets by system_name or id
        if system_name:
            mcp_server_schema = (
                await mcp_servers_service.get_with_secrets_by_system_name(system_name)
            )
        elif id:
            mcp_server_schema = await mcp_servers_service.get_with_secrets(id)
        else:
            raise ValueError("Either id or system_name must be provided")

        # Create service config with secrets
        mcp_server_config = McpServerConfigWithSecrets(
            name=mcp_server_schema.name,
            system_name=mcp_server_schema.system_name,
            transport=McpTransportProtocol(
                mcp_server_schema.transport
            ),  # Convert string to enum
            url=mcp_server_schema.url,
            headers=mcp_server_schema.headers,
            tools=None,  # MCP tools are handled internally
            secrets=mcp_server_schema.secrets_encrypted,  # These are actually unencrypted in the domain schema
        )

        return mcp_server_config


async def call_mcp_server_tool(
    tool: str,
    arguments: dict,
    mcp_server_id: str | None = None,
    mcp_server_system_name: str | None = None,
) -> CallToolResult:
    """Call MCP server tool using domain service."""

    # Get MCP server with secrets
    mcp_server_config = await get_mcp_server_with_secrets(
        id=mcp_server_id, system_name=mcp_server_system_name
    )

    session_params = get_mcp_server_session_params(mcp_server_config)

    async with init_client_session(session_params) as session:
        result = await session.call_tool(
            name=tool,
            arguments=arguments,
        )

        return result


async def test_mcp_server_connection(
    id: str | None = None,
    system_name: str | None = None,
) -> None:
    """Test MCP server connection."""

    mcp_server = await get_mcp_server_with_secrets(id, system_name)

    session_params = get_mcp_server_session_params(mcp_server)

    async with init_client_session(session_params):
        return None


async def sync_mcp_server_tools(
    id: str | None = None,
    system_name: str | None = None,
) -> list[Tool]:
    """Sync MCP server tools."""

    assert id or system_name, (
        "Cannot get MCP server - id or system_name is not provided"
    )

    mcp_server = await get_mcp_server_with_secrets(id, system_name)

    session_params = get_mcp_server_session_params(mcp_server)

    async with init_client_session(session_params) as session:
        # TODO - check pagination
        list_tools_result = await session.list_tools()

        tools_dict = list_tools_result.model_dump().get("tools")

        # Update tools in database using SQLAlchemy
        async with alchemy.get_session() as db_session:
            mcp_servers_service = MCPServersService(session=db_session)

            # Get the server ID if we only have system_name
            server_id = id
            if not server_id and system_name:
                server = await mcp_servers_service.get_one(system_name=system_name)
                server_id = server.id

            # Update tools for the MCP server
            update_data = MCPServerUpdate(tools=tools_dict)
            await mcp_servers_service.update(
                data=update_data, item_id=server_id, auto_commit=True
            )

        return list_tools_result.tools
