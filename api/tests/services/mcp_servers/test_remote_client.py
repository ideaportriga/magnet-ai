from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock

import pytest

# Warm the normal application import graph before outbound_auth is imported.
import core.config.app  # noqa: F401

from services.mcp_servers import remote_client
from services.mcp_servers.remote_client import build_mcp_request_headers
from services.mcp_servers.types import (
    McpServerConfigWithSecrets,
    McpServerSessionParams,
)
from services.outbound_auth.models import ResolvedRequestAuth, ServerConfig


@asynccontextmanager
async def _context(value: Any) -> AsyncIterator[Any]:
    yield value


def _server(**overrides: Any) -> McpServerConfigWithSecrets:
    values = {
        "name": "Test server",
        "system_name": "TEST_SERVER",
        "transport": "streamable-http",
        "url": "https://example.test/mcp",
    }
    values.update(overrides)
    return McpServerConfigWithSecrets(**values)


@pytest.mark.anyio
async def test_builds_bearer_header_and_resolves_placeholders() -> None:
    server = _server(
        headers={"X-Custom": "{CUSTOM_VALUE}"},
        security_scheme={"type": "http", "scheme": "bearer"},
        security_values={"token": "{ACCESS_TOKEN}"},
        secrets={"CUSTOM_VALUE": "custom", "ACCESS_TOKEN": "token"},
    )

    headers = await build_mcp_request_headers(server)

    assert headers == {
        "X-Custom": "custom",
        "Authorization": "Bearer token",
    }


@pytest.mark.anyio
async def test_returns_resolved_headers_without_security_scheme() -> None:
    server = _server(
        headers={"X-Custom": "{CUSTOM_VALUE}"},
        secrets={"CUSTOM_VALUE": "custom"},
    )

    headers = await build_mcp_request_headers(server)

    assert headers == {"X-Custom": "custom"}


@pytest.mark.anyio
async def test_rejects_query_or_cookie_authentication_for_mcp() -> None:
    server = _server(
        security_scheme={
            "type": "apiKey",
            "in": "query",
            "name": "api_key",
        },
        security_values={"api_key": "secret"},
    )

    with pytest.raises(ValueError, match="header placement only"):
        await build_mcp_request_headers(server)


def test_cache_key_changes_when_security_configuration_changes() -> None:
    security_scheme = {
        "type": "oauth2",
        "flows": {
            "clientCredentials": {
                "tokenUrl": "https://auth.example.test/oauth/token",
                "scopes": {},
            }
        },
        "tokenCache": {"enabled": True},
    }

    first = _server(
        security_scheme=security_scheme,
        security_values={
            "client_id": "client-id",
            "client_secret": "client-secret",
        },
    )
    second = _server(
        security_scheme=security_scheme,
        security_values={
            "client_id": "client-id",
            "client_secret": "different-secret",
        },
    )

    assert remote_client._token_cache_key(first) != remote_client._token_cache_key(
        second
    )


@pytest.mark.anyio
async def test_cache_key_is_added_to_security_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, ServerConfig | None] = {}

    async def fake_resolve(
        server_config: ServerConfig | None,
        **_: Any,
    ) -> ResolvedRequestAuth:
        captured["config"] = server_config
        return ResolvedRequestAuth(headers={"Authorization": "Bearer token"})

    monkeypatch.setattr(
        remote_client,
        "resolve_request_auth",
        fake_resolve,
    )
    server = _server(
        security_scheme={
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://auth.example.test/oauth/token",
                    "scopes": {},
                }
            },
            "tokenCache": {"enabled": True},
        },
        security_values={
            "client_id": "client-id",
            "client_secret": "client-secret",
        },
    )

    headers = await build_mcp_request_headers(server)

    config = captured["config"]
    assert config is not None
    assert config.security is not None
    assert config.security.token_cache is not None
    assert config.security.token_cache.enabled is True
    assert config.security.token_cache.key == remote_client._token_cache_key(server)
    assert headers == {"Authorization": "Bearer token"}


@pytest.mark.anyio
async def test_cache_is_disabled_without_openapi_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, ServerConfig | None] = {}

    async def fake_resolve(
        server_config: ServerConfig | None,
        **_: Any,
    ) -> ResolvedRequestAuth:
        captured["config"] = server_config
        return ResolvedRequestAuth()

    monkeypatch.setattr(
        remote_client,
        "resolve_request_auth",
        fake_resolve,
    )
    server = _server(
        security_scheme={
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://auth.example.test/oauth/token",
                    "scopes": {},
                }
            },
        },
        security_values={
            "client_id": "client-id",
            "client_secret": "client-secret",
        },
    )

    await build_mcp_request_headers(server)

    config = captured["config"]
    assert config is not None
    assert config.security is not None
    assert config.security.token_cache is None


class FakeClientSession:
    def __init__(self, read_stream: Any, write_stream: Any) -> None:
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.initialize = AsyncMock()

    async def __aenter__(self) -> FakeClientSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.mark.anyio
async def test_initializes_streamable_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clients: list[FakeClientSession] = []

    def client_session(read_stream: Any, write_stream: Any) -> FakeClientSession:
        client = FakeClientSession(read_stream, write_stream)
        clients.append(client)
        return client

    monkeypatch.setattr(
        remote_client,
        "streamablehttp_client",
        lambda *, url, headers: _context(("read", "write", "session-id")),
    )
    monkeypatch.setattr(remote_client, "ClientSession", client_session)

    params = McpServerSessionParams(
        transport="streamable-http",
        url="https://example.test/mcp",
        headers={"Authorization": "Bearer token"},
    )

    async with remote_client.init_client_session(params) as session:
        assert session is clients[0]

    assert len(clients) == 1
    assert clients[0].read_stream == "read"
    assert clients[0].write_stream == "write"
    clients[0].initialize.assert_awaited_once_with()


@pytest.mark.anyio
async def test_initializes_sse_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clients: list[FakeClientSession] = []

    def client_session(read_stream: Any, write_stream: Any) -> FakeClientSession:
        client = FakeClientSession(read_stream, write_stream)
        clients.append(client)
        return client

    monkeypatch.setattr(
        remote_client,
        "sse_client",
        lambda *, url, headers: _context(("read", "write")),
    )
    monkeypatch.setattr(remote_client, "ClientSession", client_session)

    params = McpServerSessionParams(
        transport="sse",
        url="https://example.test/sse",
        headers={"X-Custom": "value"},
    )

    async with remote_client.init_client_session(params) as session:
        assert session is clients[0]

    clients[0].initialize.assert_awaited_once_with()


@pytest.mark.anyio
async def test_rejects_unsupported_transport() -> None:
    params = McpServerSessionParams.model_construct(
        transport="unsupported",
        url="https://example.test/mcp",
        headers=None,
    )

    with pytest.raises(ValueError, match="Unsupported transport type"):
        async with remote_client.init_client_session(params):
            pass
