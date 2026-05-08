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

Registered tools (11 total):

  Read-only — prompt templates:
    prompt_templates_list       List all templates (name, system_name, description)
    prompt_template_get         Full template; active variant has text, others lean
    prompt_template_variant_get Full details for one specific variant

  Read-only — LLM monitoring:
    llm_usage_summary           Aggregate cost/latency/error stats
    llm_calls_list              Paginated individual call records

  Mutating / LLM-calling:
    prompt_template_run         Execute a template (incurs LLM cost)

  Read-only — evaluations:
    evaluation_sets_list        Paginated list of evaluation sets
    evaluation_set_get          One evaluation set with all test items
    evaluations_list            Paginated list of past evaluation runs

  Mutating:
    evaluation_set_create       Create a new evaluation set
    evaluation_run              Fire a background evaluation job
"""

from __future__ import annotations

from logging import getLogger

from mcp.server.auth.settings import (
    AuthSettings as MCPAuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl

from core.config.base import get_mcp_settings

from .auth_provider import provider as auth_provider
from .tools.evaluations import (
    evaluation_run,
    evaluation_set_create,
    evaluation_set_get,
    evaluation_sets_list,
    evaluations_list,
)
from .tools.llm_monitoring import llm_calls_list, llm_usage_summary
from .tools.prompt_execution import prompt_template_run
from .tools.prompt_templates import (
    prompt_template_get,
    prompt_template_variant_get,
    prompt_templates_list,
)

logger = getLogger(__name__)

_READ = ToolAnnotations(readOnlyHint=True, idempotentHint=True)
_WRITE = ToolAnnotations(readOnlyHint=False)
_EXEC = ToolAnnotations(readOnlyHint=False, openWorldHint=True)

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
        instructions=(
            "Magnet AI MCP server. Provides tools for prompt template discovery, "
            "LLM cost and usage monitoring, prompt execution, and evaluation management. "
            "Start with prompt_templates_list to discover available templates, then use "
            "prompt_template_get for details. Use llm_usage_summary and llm_calls_list "
            "to analyse costs and inspect LLM responses. Use evaluation_* tools to manage "
            "and run structured evaluations of prompt templates."
        ),
        auth_server_provider=auth_provider,
        auth=mcp_auth,
        stateless_http=True,
        # host="0.0.0.0" tells FastMCP this isn't a localhost-only server,
        # so it skips auto-enabling the DNS rebinding protection that would
        # restrict Host headers to 127.0.0.1/localhost only.
        host="0.0.0.0",
    )

    # Prompt template tools (read-only)
    fastmcp.tool(annotations=_READ)(prompt_templates_list)
    fastmcp.tool(annotations=_READ)(prompt_template_get)
    fastmcp.tool(annotations=_READ)(prompt_template_variant_get)

    # LLM monitoring tools (read-only)
    fastmcp.tool(annotations=_READ)(llm_usage_summary)
    fastmcp.tool(annotations=_READ)(llm_calls_list)

    # Execution tool (calls LLM — incurs cost)
    fastmcp.tool(annotations=_EXEC)(prompt_template_run)

    # Evaluation tools
    fastmcp.tool(annotations=_READ)(evaluation_sets_list)
    fastmcp.tool(annotations=_READ)(evaluation_set_get)
    fastmcp.tool(annotations=_WRITE)(evaluation_set_create)
    fastmcp.tool(annotations=_READ)(evaluations_list)
    fastmcp.tool(annotations=_EXEC)(evaluation_run)

    _fastmcp_app = fastmcp
    logger.info(
        "FastMCP initialized: issuer=%s audience=%s tools=11",
        settings.MCP_ISSUER_URL,
        settings.MCP_AUDIENCE,
    )
    return fastmcp


def build_mcp_app():
    """Return the Starlette ASGI app to mount alongside the Litestar API."""
    return get_fastmcp().streamable_http_app()
