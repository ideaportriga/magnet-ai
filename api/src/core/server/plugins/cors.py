"""CORS configuration plugin."""

import os
from logging import getLogger
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from litestar.config.cors import CORSConfig
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


def _validate_origin(raw: str) -> str | None:
    """Return a normalized origin or None if it is unsafe to use with credentials.

    Rules:
    - reject empty, whitespace-only, and the wildcard ``*`` (browsers refuse
      ``*`` together with credentials anyway, but we fail fast);
    - require ``http(s)://host[:port]`` form — no path/query/fragment;
    - strip a trailing slash so ``https://app.example.com/`` and
      ``https://app.example.com`` are treated identically.
    """
    o = raw.strip().rstrip("/")
    if not o or o == "*":
        return None
    parsed = urlparse(o)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    if parsed.path or parsed.query or parsed.fragment or parsed.params:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


class CORSPlugin(InitPluginProtocol):
    """Plugin to handle CORS configuration."""

    def __init__(self) -> None:
        self.env = os.environ
        raw_origins = self.env.get("CORS_OVERRIDE_ALLOWED_ORIGINS", "").split(",")

        validated: list[str] = []
        for raw in raw_origins:
            normalized = _validate_origin(raw)
            if normalized is None:
                if raw.strip():
                    logger.warning(
                        "CORS: dropped invalid/unsafe origin %r — must be "
                        "'scheme://host[:port]' without path; '*' is rejected "
                        "because credentials=True",
                        raw,
                    )
                continue
            validated.append(normalized)

        self.allowed_origins = validated

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure CORS settings."""
        if self.allowed_origins:
            cors_config = CORSConfig(
                allow_origins=self.allowed_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "x-api-key",
                    "x-user-id",
                    "x-request-id",
                    # MCP Streamable HTTP transport headers — sent by browser-
                    # based MCP clients (e.g. MCP Inspector at :6274).
                    "mcp-session-id",
                    "mcp-protocol-version",
                    "last-event-id",
                ],
                expose_headers=[
                    # The MCP server returns Mcp-Session-Id on the initialize
                    # response; clients have to read it to continue the session.
                    "mcp-session-id",
                ],
            )
            app_config.cors_config = cors_config

        return app_config
