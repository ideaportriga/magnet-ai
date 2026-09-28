from __future__ import annotations

import hashlib
import json

import aiohttp

from services.api_servers.types import ApiServerConfigWithSecrets
from services.outbound_auth.models import (
    ServerConfig,
    TransportConfig,
)
from services.outbound_auth.service import (
    resolve_request_auth,
    security_config_from_openapi,
    token_cache_cfg_from_openapi,
)


def _token_cache_key(api_server: ApiServerConfigWithSecrets) -> str:
    """Build a stable token cache key from the API server security configuration."""
    revision = hashlib.sha256(
        json.dumps(
            {
                "security_scheme": api_server.security_scheme,
                "security_values": api_server.security_values,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()[:12]

    return f"api_server:{api_server.name}:{revision}"


async def build_api_request_headers(
    api_server: ApiServerConfigWithSecrets,
) -> dict[str, str] | None:
    """Resolve authentication and custom headers for API server requests."""
    token_cache = token_cache_cfg_from_openapi(
        _token_cache_key(api_server),
        api_server.security_scheme,
    )
    security_config = security_config_from_openapi(
        api_server.security_scheme,
        api_server.security_values,
        token_cache=token_cache,
    )

    resolved = await resolve_request_auth(
        ServerConfig(
            security=security_config,
            transport=TransportConfig(
                verify_ssl=api_server.verify_ssl,
            ),
        ),
        base_headers=api_server.custom_headers,
        secrets=api_server.secrets,
    )

    if resolved.query or resolved.cookies:
        raise ValueError(
            "API server authentication currently supports header placement only"
        )

    return resolved.headers or None


async def create_api_client_session(
    api_server: ApiServerConfigWithSecrets,
) -> aiohttp.ClientSession:
    """Create an authenticated HTTP client session for the API server."""
    return aiohttp.ClientSession(
        headers=await build_api_request_headers(api_server),
        connector=aiohttp.TCPConnector(
            ssl=api_server.verify_ssl,
        ),
    )
