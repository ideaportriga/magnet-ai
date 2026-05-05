"""FastMCP server instance and ASGI app builder.

`build_mcp_app()` returns the Starlette ASGI app produced by
`FastMCP.streamable_http_app()`. That single app contains:

  - /authorize, /token                              (OAuth 2.1 AS endpoints)
  - /.well-known/oauth-authorization-server         (RFC 8414 metadata)
  - /.well-known/oauth-protected-resource           (RFC 9728 metadata)
  - /mcp                                            (Streamable HTTP MCP transport,
                                                     bearer-auth-protected)

`/register` and `/revoke` are intentionally NOT mounted: dynamic client
registration is disabled (admin CRUD instead), and we don't currently expose
revocation as a public endpoint.
"""

from __future__ import annotations

from logging import getLogger

from mcp.server.auth.settings import (
    AuthSettings as MCPAuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl

from core.config.base import get_mcp_settings

from .auth_provider import provider as auth_provider
from .tools.prompt_template import get_prompt_template_details

logger = getLogger(__name__)


_fastmcp_app: FastMCP | None = None


def get_fastmcp() -> FastMCP:
    """Lazy-build the FastMCP instance with auth + tools registered."""
    global _fastmcp_app
    if _fastmcp_app is not None:
        return _fastmcp_app

    settings = get_mcp_settings()
    if not settings.MCP_ENABLED:
        raise RuntimeError("get_fastmcp() called but MCP_ENABLED=false")
    if not settings.MCP_ISSUER_URL or not settings.MCP_AUDIENCE:
        raise RuntimeError(
            "MCP_ISSUER_URL and MCP_AUDIENCE must be set when MCP_ENABLED=true"
        )

    mcp_auth = MCPAuthSettings(
        issuer_url=AnyHttpUrl(settings.MCP_ISSUER_URL),
        resource_server_url=AnyHttpUrl(settings.MCP_AUDIENCE),
        # DCR explicitly disabled. Clients must be pre-registered via the
        # admin panel; see docs/MCP_CONNECTOR_SETUP.md.
        client_registration_options=ClientRegistrationOptions(enabled=False),
        revocation_options=RevocationOptions(enabled=False),
        required_scopes=None,
    )

    fastmcp = FastMCP(
        name="magnet",
        instructions=("Magnet MCP server"),
        auth_server_provider=auth_provider,
        auth=mcp_auth,
        stateless_http=True,
        # host="0.0.0.0" tells FastMCP this isn't a localhost-only server,
        # so it skips auto-enabling the DNS rebinding protection that would
        # restrict Host headers to 127.0.0.1/localhost only.
        host="0.0.0.0",
    )

    # Register tools.
    fastmcp.tool()(get_prompt_template_details)

    _fastmcp_app = fastmcp
    logger.info(
        "FastMCP initialized: issuer=%s audience=%s",
        settings.MCP_ISSUER_URL,
        settings.MCP_AUDIENCE,
    )
    return fastmcp


def build_mcp_app():
    """Return the Starlette ASGI app to mount alongside the Litestar API."""
    return get_fastmcp().streamable_http_app()
