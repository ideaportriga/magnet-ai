"""Wire the FastMCP-built Starlette sub-app into Litestar.

FastMCP returns a single Starlette app containing every route the MCP/OAuth
spec needs:

  - /authorize, /token                              (OAuth AS endpoints)
  - /.well-known/oauth-authorization-server         (RFC 8414 metadata)
  - /.well-known/oauth-protected-resource           (RFC 9728 metadata)
  - /mcp                                            (Streamable HTTP MCP transport)

We expose those paths to Litestar as five `@asgi(...)` route handlers, each of
which forwards the request to the inner Starlette app unchanged. Single-path
handlers (not `is_mount`) so Litestar leaves `scope['path']` alone — Starlette
then matches its own routes on the original path.

Lifespan: FastMCP's session manager needs `run()` invoked. We adapt it to the
Litestar `lifespan` parameter.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import asgi
from litestar.types import Receive, Scope, Send

if TYPE_CHECKING:
    from litestar import Litestar
    from starlette.applications import Starlette

logger = getLogger(__name__)

_starlette_app: Starlette | None = None


def _ensure_initialized() -> Starlette:
    """Build the FastMCP Starlette app on first call (idempotent)."""
    global _starlette_app
    if _starlette_app is not None:
        return _starlette_app

    from .server import get_fastmcp

    fastmcp = get_fastmcp()
    _starlette_app = fastmcp.streamable_http_app()
    return _starlette_app


# ── Route handlers ────────────────────────────────────────────────────────


@asgi(
    "/authorize",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_oauth_authorize(scope: Scope, receive: Receive, send: Send) -> None:
    """OAuth 2.1 /authorize endpoint (handled by MCP SDK)."""
    await _ensure_initialized()(scope, receive, send)


@asgi(
    "/token",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_oauth_token(scope: Scope, receive: Receive, send: Send) -> None:
    """OAuth 2.1 /token endpoint (handled by MCP SDK)."""
    await _ensure_initialized()(scope, receive, send)


@asgi(
    "/.well-known/oauth-authorization-server",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_oauth_as_metadata(scope: Scope, receive: Receive, send: Send) -> None:
    """RFC 8414 OAuth Authorization Server Metadata."""
    await _ensure_initialized()(scope, receive, send)


@asgi(
    "/.well-known/oauth-protected-resource",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_oauth_prm(scope: Scope, receive: Receive, send: Send) -> None:
    """RFC 9728 OAuth Protected Resource Metadata."""
    await _ensure_initialized()(scope, receive, send)


async def _forward_to_mcp(scope: Scope, receive: Receive, send: Send) -> None:
    """Forward a scope to FastMCP's Starlette app, ensuring trailing slash.

    FastMCP returns a Starlette app shaped like `Mount("/mcp", inner_app)`.
    Starlette's `Mount` issues a 307 redirect to `/mcp/` whenever it sees a
    request with `scope['path'] == '/mcp'` exactly — and since Litestar
    normalizes trailing slashes before dispatch, the redirect target loops
    back into this handler with `/mcp` again, producing a 307 → 307 → … loop.

    Rewriting `scope['path']` to `/mcp/` before forwarding makes the inner
    Mount match without redirecting, so the request reaches the streamable
    HTTP endpoint on the first hop.
    """
    if scope.get("path") in ("/mcp", "/mcp/"):
        scope = dict(scope)
        scope["path"] = "/mcp/"
        # raw_path is bytes; keep it consistent so any inner middleware
        # that prefers raw_path over path doesn't see the old value.
        if "raw_path" in scope:
            scope["raw_path"] = b"/mcp/"
    await _ensure_initialized()(scope, receive, send)


@asgi(
    "/mcp",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_mcp(scope: Scope, receive: Receive, send: Send) -> None:
    """Streamable HTTP MCP transport (Mount("/mcp", ...) inside Starlette)."""
    await _forward_to_mcp(scope, receive, send)


@asgi(
    "/mcp/",
    is_mount=False,
    copy_scope=True,
    opt={"exclude_from_auth": True},
)
async def asgi_mcp_slash(scope: Scope, receive: Receive, send: Send) -> None:
    """Trailing-slash variant — clients (Inspector, browsers following the
    Starlette Mount redirect) hit /mcp/. Same forwarding logic; declaring
    both paths keeps Litestar from normalizing one into the other and
    re-triggering the redirect loop.
    """
    await _forward_to_mcp(scope, receive, send)


# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def mcp_lifespan(app: "Litestar") -> AsyncIterator[None]:
    """Litestar lifespan that drives the FastMCP session manager.

    FastMCP wires `session_manager.run()` onto its internal Starlette app's
    lifespan. Since we're hosting the routes inside Litestar instead of running
    that Starlette app standalone, we invoke the lifespan from here.

    Per the SDK contract, `session_manager.run()` may only be called once per
    instance — `_ensure_initialized()` ensures one FastMCP/session-manager
    pair lives for the full app lifetime.
    """
    starlette_app = _ensure_initialized()
    async with starlette_app.router.lifespan_context(starlette_app):
        logger.info("MCP server lifespan active")
        yield


def get_mcp_route_handlers() -> list:
    """Return the Litestar ASGI route handlers to register on the app."""
    return [
        asgi_oauth_authorize,
        asgi_oauth_token,
        asgi_oauth_as_metadata,
        asgi_oauth_prm,
        asgi_mcp,
        asgi_mcp_slash,
    ]
