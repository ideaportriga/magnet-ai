"""Magnet's MCP server — exposes selected business logic to MCP clients.

When `MCP_ENABLED=true`, app.py mounts the FastMCP-generated ASGI sub-app at
the project root. That sub-app supplies:
  - /authorize, /token  — OAuth 2.1 authorization-server endpoints
  - /.well-known/oauth-authorization-server  — RFC 8414 metadata
  - /.well-known/oauth-protected-resource    — RFC 9728 metadata
  - /mcp  — the Streamable-HTTP MCP endpoint itself, bearer-auth-protected

User-facing login is delegated back into Magnet via the
/api/v2/auth/mcp_authorize endpoint (see api/src/routes/auth_v2.py), which
reuses the existing Microsoft / Google / local-password flows.
"""

from __future__ import annotations

__all__: list[str] = []
