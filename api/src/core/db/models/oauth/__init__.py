"""OAuth authorization-server models (used when Magnet exposes an MCP server)."""

from .oauth_authorization_code import OAuthAuthorizationCode
from .oauth_client import OAuthClient

__all__ = [
    "OAuthAuthorizationCode",
    "OAuthClient",
]
