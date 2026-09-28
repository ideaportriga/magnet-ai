from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Any

import pytest

# Initialize the normal application import graph before importing outbound_auth.
import core.config.app  # noqa: F401

from services.outbound_auth import service
from services.outbound_auth.cache import clear_cache
from services.outbound_auth.models import (
    SecurityConfig,
    ServerConfig,
    TokenCacheConfig,
    TransportConfig,
)
from services.outbound_auth.service import (
    _format_oauth_scopes,
    resolve_request_auth,
    security_config_from_openapi,
    token_cache_cfg_from_openapi,
)


@dataclass
class OAuthHttpMock:
    status: int = 200
    payload: Any = field(
        default_factory=lambda: {
            "access_token": "access-token",
            "token_type": "Bearer",
            "expires_in": 3_600,
        }
    )
    raw_body: str | None = None
    requests: list[dict[str, Any]] = field(default_factory=list)


class FakeResponse:
    url = "https://auth.example.test/oauth/token"
    headers = {"Content-Type": "application/json"}

    def __init__(self, http: OAuthHttpMock) -> None:
        self._http = http
        self.status = http.status

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def text(self) -> str:
        if self._http.raw_body is not None:
            return self._http.raw_body
        return json.dumps(self._http.payload)


class FakeSession:
    def __init__(self, http: OAuthHttpMock) -> None:
        self._http = http

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self._http.requests.append({"url": url, **kwargs})
        return FakeResponse(self._http)


@pytest.fixture(autouse=True)
def _clear_token_cache() -> None:
    clear_cache()


@pytest.fixture
def oauth_http(monkeypatch: pytest.MonkeyPatch) -> OAuthHttpMock:
    http = OAuthHttpMock()
    monkeypatch.setattr(
        service.aiohttp,
        "ClientSession",
        lambda: FakeSession(http),
    )
    return http


def _client_credentials_config(
    *,
    token_cache: TokenCacheConfig | None = None,
    token_endpoint_auth_method: str = "client_secret_post",
    verify_ssl: bool = True,
) -> ServerConfig:
    return ServerConfig(
        security=SecurityConfig(
            type="oauth2",
            values={
                "client_id": "client-id",
                "client_secret": "client-secret",
            },
            flow="client_credentials",
            token_url="https://auth.example.test/oauth/token",
            scope="read:tools write:tools",
            token_endpoint_auth_method=token_endpoint_auth_method,  # type: ignore[arg-type]
            token_cache=token_cache,
        ),
        transport=TransportConfig(verify_ssl=verify_ssl),
    )


@pytest.mark.anyio
async def test_no_security_config_resolves_base_header_placeholders() -> None:
    result = await resolve_request_auth(
        None,
        base_headers={"X-Tenant": "{TENANT}"},
        secrets={"TENANT": "tenant-1"},
    )

    assert result.headers == {"X-Tenant": "tenant-1"}
    assert result.query == {}
    assert result.cookies == {}


@pytest.mark.anyio
async def test_resolves_basic_authentication() -> None:
    config = SecurityConfig(
        type="http",
        scheme="basic",
        values={"username": "user", "password": "{PASSWORD}"},
    )

    result = await resolve_request_auth(
        ServerConfig(security=config),
        secrets={"PASSWORD": "pass"},
    )

    encoded = base64.b64encode(b"user:pass").decode()
    assert result.headers == {"Authorization": f"Basic {encoded}"}


@pytest.mark.anyio
async def test_resolves_bearer_authentication_and_overrides_base_header() -> None:
    config = SecurityConfig(
        type="http",
        scheme="bearer",
        values={"token": "new-token"},
    )

    result = await resolve_request_auth(
        ServerConfig(security=config),
        base_headers={"Authorization": "Bearer old-token"},
    )

    assert result.headers == {"Authorization": "Bearer new-token"}


@pytest.mark.parametrize(
    ("location", "attribute"),
    [
        ("header", "headers"),
        ("query", "query"),
        ("cookie", "cookies"),
    ],
)
@pytest.mark.anyio
async def test_resolves_api_key_for_supported_locations(
    location: str,
    attribute: str,
) -> None:
    config = SecurityConfig(
        type="apiKey",
        location=location,  # type: ignore[arg-type]
        name="api-key",
        values={"api_key": "secret"},
    )

    result = await resolve_request_auth(ServerConfig(security=config))

    assert getattr(result, attribute) == {"api-key": "secret"}


@pytest.mark.anyio
async def test_client_credentials_post_authentication(
    oauth_http: OAuthHttpMock,
) -> None:
    result = await resolve_request_auth(_client_credentials_config())

    assert result.headers == {"Authorization": "Bearer access-token"}
    assert oauth_http.requests == [
        {
            "url": "https://auth.example.test/oauth/token",
            "data": {
                "grant_type": "client_credentials",
                "client_id": "client-id",
                "client_secret": "client-secret",
                "scope": "read:tools write:tools",
            },
            "headers": {},
            "allow_redirects": False,
            "ssl": True,
        }
    ]


@pytest.mark.anyio
async def test_client_credentials_basic_authentication(
    oauth_http: OAuthHttpMock,
) -> None:
    config = _client_credentials_config(
        token_endpoint_auth_method="client_secret_basic",
    )

    await resolve_request_auth(config)

    request = oauth_http.requests[0]
    assert request["data"] == {
        "grant_type": "client_credentials",
        "scope": "read:tools write:tools",
    }
    assert request["headers"] == {
        "Authorization": "Basic Y2xpZW50LWlkOmNsaWVudC1zZWNyZXQ="
    }


@pytest.mark.anyio
async def test_client_credentials_disables_ssl_verification(
    oauth_http: OAuthHttpMock,
) -> None:
    config = _client_credentials_config(
        verify_ssl=False,
    )

    await resolve_request_auth(config)

    assert oauth_http.requests[0]["ssl"] is False


@pytest.mark.anyio
async def test_password_flow_authentication(
    oauth_http: OAuthHttpMock,
) -> None:
    config = ServerConfig(
        security=SecurityConfig(
            type="oauth2",
            flow="password",
            token_url="https://auth.example.test/oauth/token",
            scope="openid profile",
            values={"username": "user", "password": "pass"},
        ),
    )

    await resolve_request_auth(config)

    assert oauth_http.requests[0]["data"] == {
        "grant_type": "password",
        "username": "user",
        "password": "pass",
        "scope": "openid profile",
    }
    assert oauth_http.requests[0]["ssl"] is True


@pytest.mark.anyio
async def test_password_flow_disables_ssl_verification(
    oauth_http: OAuthHttpMock,
) -> None:
    config = ServerConfig(
        security=SecurityConfig(
            type="oauth2",
            flow="password",
            token_url="https://auth.example.test/oauth/token",
            values={"username": "user", "password": "pass"},
        ),
        transport=TransportConfig(verify_ssl=False),
    )

    await resolve_request_auth(config)

    assert oauth_http.requests[0]["ssl"] is False


@pytest.mark.anyio
async def test_oauth_cache_is_disabled_without_configuration(
    oauth_http: OAuthHttpMock,
) -> None:
    config = _client_credentials_config()

    await resolve_request_auth(config)
    await resolve_request_auth(config)

    assert len(oauth_http.requests) == 2


@pytest.mark.anyio
async def test_oauth_cache_is_disabled_by_default(
    oauth_http: OAuthHttpMock,
) -> None:
    config = _client_credentials_config(
        token_cache=TokenCacheConfig(
            key="mcp_server:server-id",
        ),
    )

    await resolve_request_auth(config)
    await resolve_request_auth(config)

    assert len(oauth_http.requests) == 2


@pytest.mark.anyio
async def test_oauth_cache_reuses_access_token(
    oauth_http: OAuthHttpMock,
) -> None:
    config = _client_credentials_config(
        token_cache=TokenCacheConfig(
            key="mcp_server:server-id",
            enabled=True,
        ),
    )

    first, second = await asyncio.gather(
        resolve_request_auth(config),
        resolve_request_auth(config),
    )

    assert first.headers == second.headers
    assert len(oauth_http.requests) == 1


@pytest.mark.anyio
async def test_oauth_cache_uses_fallback_ttl(
    oauth_http: OAuthHttpMock,
) -> None:
    oauth_http.payload = {
        "access_token": "access-token",
        "token_type": "Bearer",
    }
    config = _client_credentials_config(
        token_cache=TokenCacheConfig(
            key="mcp_server:server-id",
            enabled=True,
            expires_in=300,
        ),
    )

    await resolve_request_auth(config)
    await resolve_request_auth(config)

    assert len(oauth_http.requests) == 1


@pytest.mark.anyio
async def test_oauth_cache_does_not_store_token_inside_expiry_skew(
    oauth_http: OAuthHttpMock,
) -> None:
    oauth_http.payload["expires_in"] = 30
    config = _client_credentials_config(
        token_cache=TokenCacheConfig(
            key="mcp_server:server-id",
            enabled=True,
            expiry_skew=60,
        ),
    )

    await resolve_request_auth(config)
    await resolve_request_auth(config)

    assert len(oauth_http.requests) == 2


@pytest.mark.anyio
async def test_oauth_error_includes_status_and_response_body(
    oauth_http: OAuthHttpMock,
) -> None:
    oauth_http.status = 400
    oauth_http.payload = {
        "error": "invalid_client",
        "error_description": "Bad credentials",
    }

    with pytest.raises(
        RuntimeError,
        match="OAuth2 token request failed with status 400.*invalid_client",
    ):
        await resolve_request_auth(_client_credentials_config())


@pytest.mark.anyio
async def test_oauth_rejects_invalid_json(oauth_http: OAuthHttpMock) -> None:
    oauth_http.raw_body = "not-json"

    with pytest.raises(RuntimeError, match="did not return valid JSON"):
        await resolve_request_auth(_client_credentials_config())


@pytest.mark.anyio
async def test_oauth_rejects_json_that_is_not_an_object(
    oauth_http: OAuthHttpMock,
) -> None:
    oauth_http.payload = ["not", "an", "object"]

    with pytest.raises(RuntimeError, match="did not return a JSON object"):
        await resolve_request_auth(_client_credentials_config())


@pytest.mark.anyio
async def test_oauth_requires_access_token(oauth_http: OAuthHttpMock) -> None:
    oauth_http.payload = {"token_type": "Bearer", "expires_in": 3_600}

    with pytest.raises(RuntimeError, match="No access_token"):
        await resolve_request_auth(_client_credentials_config())


def test_security_config_from_openapi_client_credentials() -> None:
    config = security_config_from_openapi(
        {
            "type": "oauth2",
            "tokenEndpointAuthMethod": "client_secret_basic",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://auth.example.test/oauth/token",
                    "scopes": {
                        "read:tools": "Read tools",
                        "write:tools": "Write tools",
                    },
                }
            },
        },
        {"client_id": "id", "client_secret": "secret"},
    )

    assert config == SecurityConfig(
        type="oauth2",
        values={"client_id": "id", "client_secret": "secret"},
        flow="client_credentials",
        token_url="https://auth.example.test/oauth/token",
        scope="read:tools write:tools",
        token_endpoint_auth_method="client_secret_basic",
    )


def test_security_config_from_openapi_http_scheme_is_case_insensitive() -> None:
    config = security_config_from_openapi(
        {"type": "http", "scheme": "Bearer"},
        {"token": "token"},
    )

    assert config.scheme == "bearer"


def test_security_config_from_openapi_api_key() -> None:
    config = security_config_from_openapi(
        {"type": "apiKey", "in": "query", "name": "api_key"},
        {"api_key": "secret"},
    )

    assert config.type == "apiKey"
    assert config.location == "query"
    assert config.name == "api_key"


@pytest.mark.parametrize(
    ("scheme", "error"),
    [
        ({"type": "unknown"}, "Supported security scheme types"),
        (
            {"type": "oauth2", "flows": {"authorizationCode": {}}},
            "Supported OAuth2 flow values",
        ),
        (
            {"type": "http", "scheme": "digest"},
            "Supported HTTP auth scheme values",
        ),
        (
            {"type": "apiKey", "in": "body", "name": "key"},
            "Supported API key locations",
        ),
    ],
)
def test_security_config_from_openapi_rejects_unsupported_values(
    scheme: dict[str, Any],
    error: str,
) -> None:
    with pytest.raises((ValueError, NotImplementedError), match=error):
        security_config_from_openapi(scheme)


def test_token_cache_config_from_openapi_returns_none_without_extension() -> None:
    assert token_cache_cfg_from_openapi("mcp_server:id", {}) is None


def test_token_cache_config_from_openapi_uses_defaults() -> None:
    config = token_cache_cfg_from_openapi(
        "mcp_server:id",
        {"tokenCache": {}},
    )

    assert config == TokenCacheConfig(
        key="mcp_server:id",
        enabled=True,
        expiry_skew=60,
        expires_in=None,
    )


def test_token_cache_config_from_openapi_reads_custom_values() -> None:
    config = token_cache_cfg_from_openapi(
        "mcp_server:id:updated-at",
        {
            "tokenCache": {
                "enabled": False,
                "expirySkew": 30,
                "expiresIn": 300,
            }
        },
    )

    assert config == TokenCacheConfig(
        key="mcp_server:id:updated-at",
        enabled=False,
        expiry_skew=30,
        expires_in=300,
    )


@pytest.mark.parametrize(
    ("extension", "error"),
    [
        (True, "extension must be an object"),
        ({"enabled": "yes"}, "extension.enabled must be a boolean"),
        (
            {"expirySkew": -1},
            "extension.expirySkew must be a non-negative number",
        ),
        (
            {"expiresIn": 0},
            "extension.expiresIn must be a positive number",
        ),
    ],
)
def test_token_cache_config_from_openapi_rejects_invalid_values(
    extension: Any,
    error: str,
) -> None:
    with pytest.raises(ValueError, match=error):
        token_cache_cfg_from_openapi(
            "mcp_server:id",
            {"tokenCache": extension},
        )


@pytest.mark.parametrize(
    "scopes, expected",
    [
        (None, None),
        ({}, None),
        ([], None),
        ("", None),
        ("   ", None),
        ("read", "read"),
        ("  read  ", "read"),
        (["read", "write"], "read write"),
        (["read", "  ", "write"], "read write"),
        ({"read": "Read", "write": "Write"}, "read write"),
        (
            {"https://api.loganalytics.io/.default": "Access Azure Log Analytics"},
            "https://api.loganalytics.io/.default",
        ),
        (123, None),
    ],
)
def test_format_oauth_scopes(scopes, expected):
    assert _format_oauth_scopes(scopes) == expected
