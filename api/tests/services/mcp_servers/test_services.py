from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock

import pytest

# Warm the normal application import graph before MCP services are imported.
import core.config.app  # noqa: F401

from services.mcp_servers import services
from services.mcp_servers.types import (
    McpServerConfigWithSecrets,
    McpServerSessionParams,
)

SERVER_ID = "01a0c397-a7b1-7ae3-b24a-1bfcab5f057c"
CREATED_AT = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 9, 22, 12, 30, tzinfo=timezone.utc)


@asynccontextmanager
async def _context(value: Any) -> AsyncIterator[Any]:
    yield value


def _server(**overrides: Any) -> McpServerConfigWithSecrets:
    values = {
        "name": "Test server",
        "system_name": "TEST_SERVER",
        "transport": "streamable-http",
        "url": "https://example.test/mcp",
        "headers": {"X-Custom": "value"},
        "security_scheme": {"type": "http", "scheme": "bearer"},
        "security_values": {"token": "token"},
        "secrets": {"SECRET": "secret"},
    }
    values.update(overrides)
    return McpServerConfigWithSecrets(**values)


def _domain_server() -> SimpleNamespace:
    return SimpleNamespace(
        id=SERVER_ID,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
        name="Test server",
        system_name="TEST_SERVER",
        transport="streamable-http",
        url="https://example.test/mcp",
        headers={"X-Custom": "{CUSTOM}"},
        security_scheme={"type": "http", "scheme": "bearer"},
        security_values={"token": "{ACCESS_TOKEN}"},
        secrets_encrypted={
            "CUSTOM": "custom",
            "ACCESS_TOKEN": "token",
        },
    )


@pytest.mark.anyio
async def test_get_session_params_builds_authenticated_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _server()
    build_headers = AsyncMock(return_value={"Authorization": "Bearer token"})
    monkeypatch.setattr(
        services,
        "build_mcp_request_headers",
        build_headers,
    )

    result = await services.get_mcp_server_session_params(server)

    assert result == McpServerSessionParams(
        transport="streamable-http",
        url="https://example.test/mcp",
        headers={"Authorization": "Bearer token"},
    )
    build_headers.assert_awaited_once_with(server)


@pytest.mark.anyio
async def test_get_server_with_secrets_by_id_maps_domain_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain_server = _domain_server()
    domain_service = SimpleNamespace(
        get_with_secrets=AsyncMock(return_value=domain_server),
        get_with_secrets_by_system_name=AsyncMock(),
    )
    db_session = object()

    monkeypatch.setattr(
        services.alchemy,
        "get_session",
        lambda: _context(db_session),
    )
    monkeypatch.setattr(
        services,
        "MCPServersService",
        lambda *, session: domain_service,
    )

    result = await services.get_mcp_server_with_secrets(id=SERVER_ID)

    domain_service.get_with_secrets.assert_awaited_once_with(SERVER_ID)
    domain_service.get_with_secrets_by_system_name.assert_not_awaited()
    assert result.security_scheme == domain_server.security_scheme
    assert result.security_values == domain_server.security_values
    assert result.secrets == domain_server.secrets_encrypted


@pytest.mark.anyio
async def test_get_server_with_secrets_by_system_name_uses_name_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain_server = _domain_server()
    domain_service = SimpleNamespace(
        get_with_secrets=AsyncMock(),
        get_with_secrets_by_system_name=AsyncMock(return_value=domain_server),
    )

    monkeypatch.setattr(
        services.alchemy,
        "get_session",
        lambda: _context(object()),
    )
    monkeypatch.setattr(
        services,
        "MCPServersService",
        lambda *, session: domain_service,
    )

    result = await services.get_mcp_server_with_secrets(system_name="TEST_SERVER")

    domain_service.get_with_secrets_by_system_name.assert_awaited_once_with(
        "TEST_SERVER"
    )
    domain_service.get_with_secrets.assert_not_awaited()
    assert result.system_name == "TEST_SERVER"


@pytest.mark.anyio
async def test_get_server_requires_id_or_system_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        services.alchemy,
        "get_session",
        lambda: _context(object()),
    )
    monkeypatch.setattr(
        services,
        "MCPServersService",
        lambda *, session: SimpleNamespace(),
    )

    with pytest.raises(
        ValueError,
        match="Either id or system_name must be provided",
    ):
        await services.get_mcp_server_with_secrets()


@pytest.mark.anyio
async def test_call_tool_opens_session_and_returns_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _server()
    params = McpServerSessionParams(
        transport="streamable-http",
        url=server.url,
        headers={"Authorization": "Bearer token"},
    )
    expected_result = object()
    client = SimpleNamespace(
        call_tool=AsyncMock(return_value=expected_result),
    )
    get_server = AsyncMock(return_value=server)
    get_params = AsyncMock(return_value=params)

    monkeypatch.setattr(
        services,
        "get_mcp_server_with_secrets",
        get_server,
    )
    monkeypatch.setattr(
        services,
        "get_mcp_server_session_params",
        get_params,
    )
    monkeypatch.setattr(
        services,
        "init_client_session",
        lambda received: _context(client),
    )

    result = await services.call_mcp_server_tool(
        tool="fetch",
        arguments={"url": "https://example.test"},
        mcp_server_id=SERVER_ID,
    )

    assert result is expected_result
    get_server.assert_awaited_once_with(
        id=SERVER_ID,
        system_name=None,
    )
    get_params.assert_awaited_once_with(server)
    client.call_tool.assert_awaited_once_with(
        name="fetch",
        arguments={"url": "https://example.test"},
    )


@pytest.mark.anyio
async def test_connection_test_initializes_remote_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _server()
    params = McpServerSessionParams(
        transport="streamable-http",
        url=server.url,
    )
    entered: list[McpServerSessionParams] = []

    @asynccontextmanager
    async def client_context(
        received: McpServerSessionParams,
    ) -> AsyncIterator[object]:
        entered.append(received)
        yield object()

    monkeypatch.setattr(
        services,
        "get_mcp_server_with_secrets",
        AsyncMock(return_value=server),
    )
    monkeypatch.setattr(
        services,
        "get_mcp_server_session_params",
        AsyncMock(return_value=params),
    )
    monkeypatch.setattr(services, "init_client_session", client_context)

    result = await services.test_mcp_server_connection(id=SERVER_ID)

    assert result is None
    assert entered == [params]


@pytest.mark.anyio
async def test_sync_tools_updates_database_and_returns_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _server()
    params = McpServerSessionParams(
        transport="streamable-http",
        url=server.url,
    )
    tools = [
        SimpleNamespace(
            name="fetch",
            description="Fetch a URL",
            inputSchema={"type": "object"},
        )
    ]
    tools_dict = [
        {
            "name": "fetch",
            "description": "Fetch a URL",
            "inputSchema": {"type": "object"},
        }
    ]
    list_tools_result = SimpleNamespace(
        tools=tools,
        model_dump=lambda: {"tools": tools_dict},
    )
    client = SimpleNamespace(
        list_tools=AsyncMock(return_value=list_tools_result),
    )
    domain_service = SimpleNamespace(
        get_one=AsyncMock(return_value=SimpleNamespace(id=SERVER_ID)),
        update=AsyncMock(),
    )

    monkeypatch.setattr(
        services,
        "get_mcp_server_with_secrets",
        AsyncMock(return_value=server),
    )
    monkeypatch.setattr(
        services,
        "get_mcp_server_session_params",
        AsyncMock(return_value=params),
    )
    monkeypatch.setattr(
        services,
        "init_client_session",
        lambda received: _context(client),
    )
    monkeypatch.setattr(
        services.alchemy,
        "get_session",
        lambda: _context(object()),
    )
    monkeypatch.setattr(
        services,
        "MCPServersService",
        lambda *, session: domain_service,
    )

    result = await services.sync_mcp_server_tools(system_name="TEST_SERVER")

    assert result == tools
    client.list_tools.assert_awaited_once_with()
    domain_service.get_one.assert_awaited_once_with(system_name="TEST_SERVER")
    domain_service.update.assert_awaited_once()
    update_call = domain_service.update.await_args
    assert update_call.kwargs["item_id"] == SERVER_ID
    assert update_call.kwargs["auto_commit"] is True
    assert update_call.kwargs["data"].tools == tools_dict


@pytest.mark.anyio
async def test_sync_tools_uses_explicit_id_without_second_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _server()
    params = McpServerSessionParams(
        transport="streamable-http",
        url=server.url,
    )
    list_tools_result = SimpleNamespace(
        tools=[],
        model_dump=lambda: {"tools": []},
    )
    client = SimpleNamespace(
        list_tools=AsyncMock(return_value=list_tools_result),
    )
    domain_service = SimpleNamespace(
        get_one=AsyncMock(),
        update=AsyncMock(),
    )

    monkeypatch.setattr(
        services,
        "get_mcp_server_with_secrets",
        AsyncMock(return_value=server),
    )
    monkeypatch.setattr(
        services,
        "get_mcp_server_session_params",
        AsyncMock(return_value=params),
    )
    monkeypatch.setattr(
        services,
        "init_client_session",
        lambda received: _context(client),
    )
    monkeypatch.setattr(
        services.alchemy,
        "get_session",
        lambda: _context(object()),
    )
    monkeypatch.setattr(
        services,
        "MCPServersService",
        lambda *, session: domain_service,
    )

    result = await services.sync_mcp_server_tools(id=SERVER_ID)

    assert result == []
    domain_service.get_one.assert_not_awaited()
    assert domain_service.update.await_args.kwargs["item_id"] == SERVER_ID


@pytest.mark.anyio
async def test_sync_tools_requires_id_or_system_name() -> None:
    with pytest.raises(
        AssertionError,
        match="id or system_name is not provided",
    ):
        await services.sync_mcp_server_tools()
