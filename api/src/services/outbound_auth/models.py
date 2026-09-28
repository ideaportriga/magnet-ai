from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, get_args


SecurityType = Literal[
    "oauth2",
    "http",
    "apiKey",
]
SECURITY_TYPES = get_args(SecurityType)


SecurityLocation = Literal[
    "header",
    "query",
    "cookie",
]
SECURITY_LOCATIONS = get_args(SecurityLocation)


HttpAuthScheme = Literal[
    "basic",
    "bearer",
]
HTTP_AUTH_SCHEMES = get_args(HttpAuthScheme)


OAuthFlow = Literal[
    "password",
    "client_credentials",
]
OAUTH_FLOWS = get_args(OAuthFlow)


TokenEndpointAuthMethod = Literal[
    "client_secret_post",
    "client_secret_basic",
]
TOKEN_ENDPOINT_AUTH_METHODS = get_args(TokenEndpointAuthMethod)


@dataclass(frozen=True, slots=True)
class TokenCacheConfig:
    """Configure caching behavior for an OAuth access token."""

    key: str
    enabled: bool = False
    expiry_skew: float = 60
    expires_in: float | None = 3600


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Normalized authentication configuration for an outbound request."""

    type: SecurityType
    values: dict[str, Any] = field(default_factory=dict)

    # HTTP / API key
    scheme: HttpAuthScheme | None = None
    location: SecurityLocation | None = None
    name: str | None = None

    # OAuth2
    flow: OAuthFlow | None = None
    token_url: str | None = None
    scope: str | None = None
    token_endpoint_auth_method: TokenEndpointAuthMethod = "client_secret_post"

    # Optional OAuth token caching
    token_cache: TokenCacheConfig | None = None


@dataclass(frozen=True, slots=True)
class TransportConfig:
    """Configure HTTP transport behavior for an outbound request."""

    verify_ssl: bool = True


@dataclass(frozen=True, slots=True)
class ServerConfig:
    """Configure security and transport behavior for an outbound server."""

    security: SecurityConfig | None = None
    transport: TransportConfig = field(default_factory=TransportConfig)


@dataclass(slots=True)
class ResolvedRequestAuth:
    """Authentication data ready to apply to an outbound HTTP request."""

    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OAuthToken:
    """Represent an OAuth access token and its optional lifetime."""

    token_type: str
    access_token: str
    expires_in: float | None = None
