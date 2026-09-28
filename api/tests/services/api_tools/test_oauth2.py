"""OAuth2 clientCredentials scope handling for API Servers.

Exercises the token-acquisition path in
``services.api_servers.clients`` with a fake aiohttp stack:
  - OpenAPI-style ``flows.clientCredentials.scopes`` (a ``{scope: desc}``
    mapping) is flattened to a space-separated ``scope`` form field,
  - multiple scope keys join with a single space,
  - a missing/empty ``scopes`` preserves the legacy request body (no
    ``scope`` field),
  - the Azure Log Analytics schema sends exactly
    ``"https://api.loganalytics.io/.default"``,
  - a >=400 token response surfaces the provider error body without
    leaking the posted client secret.
"""

from __future__ import annotations

import json
import pytest

# Warm the import graph before the module under test is touched (same
# pre-existing circular-import chain guarded elsewhere in the suite).
import core.config.app  # noqa: F401

from services.api_servers import clients
from services.api_servers.types import ApiServerConfigWithSecrets


class _FakeResponse:
    def __init__(self, status: int = 200, payload: dict | None = None, text: str = ""):
        self.status = status
        self._payload = payload if payload is not None else {}
        self._text = text or json.dumps(self._payload)
        self.url = "https://token.example/oauth"
        self.headers = {"Content-Type": "application/json"}

    async def json(self) -> dict:
        return self._payload

    async def text(self) -> str:
        return self._text

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False


class _FakeSession:
    """aiohttp.ClientSession stand-in that records POST bodies.

    The token-acquisition helper opens a temp session (posts to the token
    URL) and then constructs a second session it returns to the caller.
    Both are represented by this class; ``posts`` on the *first* instance
    captures the token request body.
    """

    instances: list["_FakeSession"] = []

    def __init__(self, *, response: _FakeResponse | None = None, **kwargs):
        self.kwargs = kwargs
        self.posts: list[tuple[str, dict]] = []
        self._response = response or _FakeResponse(payload={"access_token": "tok-123"})
        _FakeSession.instances.append(self)

    def post(self, url: str, data: dict | None = None, **kwargs) -> _FakeResponse:
        self.posts.append((url, data or {}))
        return self._response

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False


@pytest.fixture
def fake_aiohttp(monkeypatch):
    """Patch the aiohttp stack in the clients module.

    Returns a callable that installs a token response and yields the list
    of created sessions so a test can assert on the captured POST body.
    """

    def install(token_response: _FakeResponse | None = None) -> list[_FakeSession]:
        _FakeSession.instances = []

        def session_factory(**kwargs):
            # The first session is the temp one that talks to the token URL;
            # give it the (possibly error) token response. Later sessions are
            # the returned client and need no canned response.
            resp = token_response if not _FakeSession.instances else None
            return _FakeSession(response=resp, **kwargs)

        monkeypatch.setattr(clients.aiohttp, "ClientSession", session_factory)
        monkeypatch.setattr(clients.aiohttp, "TCPConnector", lambda *a, **k: object())
        return _FakeSession.instances

    return install


def _token_body(sessions: list[_FakeSession]) -> dict:
    """Return the form body posted to the token endpoint."""
    assert sessions, "no aiohttp session was created"
    posts = sessions[0].posts
    assert posts, "no POST was made to the token endpoint"
    return posts[0][1]


def _api_server(scope=None) -> ApiServerConfigWithSecrets:
    scopes = {}
    if scope:
        scopes = {value: "" for value in scope.split()}

    return ApiServerConfigWithSecrets(
        name="Test API",
        system_name="test_api",
        url="https://api.example",
        security_scheme={
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "scopes": scopes,
                    "tokenUrl": "https://token.example/oauth",
                }
            },
        },
        security_values={"client_id": "cid", "client_secret": "super-secret"},
        secrets={},
    )


# --------------------------------------------------------------------------- #
# build_api_request_headers — token request body
# --------------------------------------------------------------------------- #


@pytest.mark.anyio
async def test_scope_is_sent_as_form_field(fake_aiohttp):
    sessions = fake_aiohttp()

    await clients.build_api_request_headers(
        _api_server("read write"),
    )

    body = _token_body(sessions)
    assert body["grant_type"] == "client_credentials"
    assert body["client_id"] == "cid"
    assert body["scope"] == "read write"


@pytest.mark.anyio
async def test_missing_scope_preserves_legacy_body(fake_aiohttp):
    sessions = fake_aiohttp()

    await clients.build_api_request_headers(
        _api_server(),
    )

    body = _token_body(sessions)
    assert "scope" not in body
    assert body == {
        "grant_type": "client_credentials",
        "client_id": "cid",
        "client_secret": "super-secret",
    }


@pytest.mark.anyio
async def test_token_error_surfaces_body_without_secret(fake_aiohttp):
    error_body = "AADSTS70011: The provided scope is not valid."
    sessions = fake_aiohttp(_FakeResponse(status=400, text=error_body))

    server = _api_server("bad")

    with pytest.raises(RuntimeError) as excinfo:
        await clients.build_api_request_headers(server)

    message = str(excinfo.value)
    assert "400" in message
    assert "AADSTS70011" in message
    assert "super-secret" not in message
    # A POST was still attempted before the failure.
    assert sessions[0].posts


# --------------------------------------------------------------------------- #
# create_api_client_session — end-to-end OpenAPI schema path
# --------------------------------------------------------------------------- #


def _azure_api_server() -> ApiServerConfigWithSecrets:
    return ApiServerConfigWithSecrets(
        name="Azure Log Analytics",
        system_name="azure_log_analytics",
        url="https://api.loganalytics.io",
        security_scheme={
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "scopes": {
                        "https://api.loganalytics.io/.default": (
                            "Access Azure Log Analytics"
                        )
                    },
                    "tokenUrl": (
                        "https://login.microsoftonline.com/tenant/oauth2/v2.0/token"
                    ),
                }
            },
        },
        security_values={"client_id": "cid", "client_secret": "secret"},
        secrets={},
    )


@pytest.mark.anyio
async def test_azure_log_analytics_schema_sends_exact_scope(fake_aiohttp):
    sessions = fake_aiohttp()

    await clients.create_api_client_session(_azure_api_server())

    body = _token_body(sessions)
    assert body["scope"] == "https://api.loganalytics.io/.default"
    assert body["grant_type"] == "client_credentials"


@pytest.mark.anyio
async def test_multiple_dict_scopes_joined_with_spaces(fake_aiohttp):
    server = _azure_api_server()
    assert server.security_scheme is not None
    server.security_scheme["flows"]["clientCredentials"]["scopes"] = {
        "https://api.loganalytics.io/.default": "a",
        "offline_access": "b",
    }
    sessions = fake_aiohttp()

    await clients.create_api_client_session(server)

    body = _token_body(sessions)
    assert body["scope"] == "https://api.loganalytics.io/.default offline_access"


@pytest.mark.anyio
async def test_no_scopes_in_schema_preserves_legacy_body(fake_aiohttp):
    server = _azure_api_server()
    assert server.security_scheme is not None
    del server.security_scheme["flows"]["clientCredentials"]["scopes"]
    sessions = fake_aiohttp()

    await clients.create_api_client_session(server)

    body = _token_body(sessions)
    assert "scope" not in body
