from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from typing import Any, cast

import aiohttp

from services.outbound_auth.cache import (
    cache_value,
    get_cached_value,
    get_cache_lock,
)
from services.outbound_auth.models import (
    HTTP_AUTH_SCHEMES,
    OAUTH_FLOWS,
    SECURITY_LOCATIONS,
    SECURITY_TYPES,
    TOKEN_ENDPOINT_AUTH_METHODS,
    HttpAuthScheme,
    OAuthFlow,
    OAuthToken,
    ResolvedRequestAuth,
    SecurityConfig,
    SecurityLocation,
    ServerConfig,
    TokenCacheConfig,
    TokenEndpointAuthMethod,
)
from utils.secrets import replace_placeholders_in_dict


def _format_oauth_scopes(scopes: Any) -> str | None:
    """Normalize OpenAPI-style OAuth2 scopes into a space-separated string.

    Accepts a plain string, a list of scope strings, or an OpenAPI
    ``scopes`` mapping (``{scope: description}``). Returns ``None`` when no
    usable scope is present so the token request preserves legacy behavior.
    """
    if not scopes:
        return None
    if isinstance(scopes, str):
        return scopes.strip() or None
    if isinstance(scopes, list):
        values = [str(scope).strip() for scope in scopes if str(scope).strip()]
        return " ".join(values) or None
    if isinstance(scopes, dict):
        values = [str(scope).strip() for scope in scopes.keys() if str(scope).strip()]
        return " ".join(values) or None
    return None


def _required_string(value: Any, field_name: str) -> str:
    """Return a required non-empty string value."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} is required")
    return value


def _required_security_value(values: Mapping[str, Any], key: str) -> str:
    """Return a required string value from the security values mapping."""
    return _required_string(values.get(key), f"Security value '{key}'")


async def resolve_request_auth(
    server_config: ServerConfig | None,
    *,
    base_headers: Mapping[str, str] | None = None,
    secrets: Mapping[str, str] | None = None,
) -> ResolvedRequestAuth:
    """Resolve authentication data for an outbound HTTP request."""
    resolved_secrets = dict(secrets or {})
    headers = replace_placeholders_in_dict(
        dict(base_headers or {}),
        resolved_secrets,
    )
    result = ResolvedRequestAuth(headers=headers)

    if server_config is None or server_config.security is None:
        return result

    security_config = server_config.security

    values = replace_placeholders_in_dict(
        security_config.values,
        resolved_secrets,
    )

    if security_config.type == "oauth2":
        token = await _resolve_oauth_access_token(
            server_config,
            values,
        )
        result.headers["Authorization"] = f"{token.token_type} {token.access_token}"
        return result

    if security_config.type == "http":
        if security_config.scheme == "basic":
            username = _required_security_value(values, "username")
            password = _required_security_value(values, "password")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            result.headers["Authorization"] = f"Basic {credentials}"
            return result

        if security_config.scheme == "bearer":
            token = _required_security_value(values, "token")
            result.headers["Authorization"] = f"Bearer {token}"
            return result

        raise ValueError("HTTP auth scheme is not configured")

    if security_config.type == "apiKey":
        name = _required_string(security_config.name, "API key name")
        api_key = _required_security_value(values, "api_key")

        if security_config.location == "header":
            result.headers[name] = api_key
        elif security_config.location == "query":
            result.query[name] = api_key
        elif security_config.location == "cookie":
            result.cookies[name] = api_key
        else:
            raise ValueError("API key location is not configured")

        return result

    raise NotImplementedError(f"Unsupported security type: {security_config.type}")


async def _resolve_oauth_access_token(
    server_config: ServerConfig,
    values: Mapping[str, Any],
) -> OAuthToken:
    """Return a cached OAuth token when available, otherwise request a new one."""
    security_config = server_config.security
    cache_cfg = security_config.token_cache

    if cache_cfg is None or not cache_cfg.enabled:
        return await _get_oauth_access_token(
            server_config,
            values,
        )

    async with get_cache_lock(cache_cfg.key):
        cached = get_cached_value(
            cache_cfg.key,
            skew_seconds=cache_cfg.expiry_skew,
        )
        if isinstance(cached, OAuthToken):
            return cached

        token = await _get_oauth_access_token(
            server_config,
            values,
        )
        ttl = token.expires_in or cache_cfg.expires_in

        if ttl is not None and ttl > cache_cfg.expiry_skew:
            cache_value(
                cache_cfg.key,
                token,
                ttl_seconds=ttl,
            )

        return token


async def _get_oauth_access_token(
    server_config: ServerConfig,
    values: Mapping[str, Any],
) -> OAuthToken:
    """Request an OAuth access token using the configured grant flow."""
    security_config = server_config.security
    if security_config.flow == "password":
        return await _get_password_access_token(
            server_config,
            values,
        )

    if security_config.flow == "client_credentials":
        return await _get_client_credentials_access_token(
            server_config,
            values,
        )

    raise ValueError("OAuth2 flow is not configured")


async def _get_password_access_token(
    server_config: ServerConfig,
    values: Mapping[str, Any],
) -> OAuthToken:
    """Request an OAuth access token using the password grant."""
    security_config = server_config.security
    transport_config = server_config.transport
    token_url = _required_string(security_config.token_url, "OAuth2 tokenUrl")
    request_data = {
        "grant_type": "password",
        "username": _required_security_value(values, "username"),
        "password": _required_security_value(values, "password"),
    }

    if security_config.scope:
        request_data["scope"] = security_config.scope

    return await _request_oauth_token(
        token_url,
        request_data,
        verify_ssl=transport_config.verify_ssl,
    )


async def _get_client_credentials_access_token(
    server_config: ServerConfig,
    values: Mapping[str, Any],
) -> OAuthToken:
    """Request an OAuth access token using the client credentials grant."""
    security_config = server_config.security
    transport_config = server_config.transport
    token_url = _required_string(security_config.token_url, "OAuth2 tokenUrl")
    client_id = _required_security_value(values, "client_id")
    client_secret = _required_security_value(values, "client_secret")

    request_data = {"grant_type": "client_credentials"}
    request_headers: dict[str, str] = {}

    if security_config.token_endpoint_auth_method == "client_secret_post":
        request_data["client_id"] = client_id
        request_data["client_secret"] = client_secret
    elif security_config.token_endpoint_auth_method == "client_secret_basic":
        request_headers["Authorization"] = aiohttp.BasicAuth(
            client_id,
            client_secret,
        ).encode()
    else:
        raise NotImplementedError(
            "Unsupported OAuth2 token endpoint auth method: "
            f"{security_config.token_endpoint_auth_method}"
        )

    if security_config.scope:
        request_data["scope"] = security_config.scope

    return await _request_oauth_token(
        token_url,
        request_data,
        request_headers=request_headers,
        verify_ssl=transport_config.verify_ssl,
    )


async def _request_oauth_token(
    token_url: str,
    request_data: Mapping[str, str],
    *,
    request_headers: Mapping[str, str] | None = None,
    verify_ssl: bool = True,
) -> OAuthToken:
    """Send an OAuth token request and parse the access token response."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            token_url,
            data=dict(request_data),
            headers=dict(request_headers or {}),
            allow_redirects=False,
            ssl=bool(verify_ssl),
        ) as response:
            body = await response.text()

            if response.status < 200 or response.status >= 300:
                raise RuntimeError(
                    "OAuth2 token request failed with status "
                    f"{response.status}: {body[:2000]}"
                )

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "OAuth2 token endpoint did not return valid JSON "
                    f"(status={response.status}, "
                    f"url={response.url}, "
                    "content_type="
                    f"{response.headers.get('Content-Type', 'missing')})"
                ) from exc

            if not isinstance(payload, dict):
                raise RuntimeError("OAuth2 token endpoint did not return a JSON object")

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("No access_token in OAuth2 response")

    token_type = payload.get("token_type", "Bearer")
    if not isinstance(token_type, str) or not token_type:
        token_type = "Bearer"

    expires_in = payload.get("expires_in")
    if expires_in is not None:
        try:
            expires_in = float(expires_in)
        except (TypeError, ValueError):
            expires_in = None
        else:
            if expires_in <= 0:
                expires_in = None

    return OAuthToken(
        token_type=token_type,
        access_token=access_token,
        expires_in=expires_in,
    )


def security_config_from_openapi(
    security_scheme: Mapping[str, Any] | None,
    values: Mapping[str, Any] | None = None,
    *,
    token_cache: TokenCacheConfig | None = None,
) -> SecurityConfig | None:
    """Create normalized auth configuration from an OpenAPI security scheme."""
    if security_scheme is None:
        return None

    scheme_type = _required_string(
        security_scheme.get("type"),
        "Security scheme type",
    )

    if scheme_type not in SECURITY_TYPES:
        raise NotImplementedError(
            f"Supported security scheme types: {', '.join(SECURITY_TYPES)}"
        )

    security_values = dict(values or {})

    if scheme_type == "oauth2":
        flows = security_scheme.get("flows")
        if not isinstance(flows, Mapping):
            raise ValueError("OAuth2 flows are not configured")

        flow_type: OAuthFlow

        if "password" in flows:
            flow_type = "password"
            flow = flows["password"]
        elif "clientCredentials" in flows:
            flow_type = "client_credentials"
            flow = flows["clientCredentials"]
        else:
            raise NotImplementedError(
                f"Supported OAuth2 flow values: {', '.join(OAUTH_FLOWS)}"
            )

        if not isinstance(flow, Mapping):
            raise ValueError("OAuth2 flow is invalid")

        token_auth_method = "client_secret_post"

        if flow_type == "client_credentials":
            token_auth_method = security_scheme.get(
                "tokenEndpointAuthMethod",
                token_auth_method,
            )
            token_auth_method = security_values.get(
                "token_endpoint_auth_method",
                token_auth_method,
            )

            if token_auth_method not in TOKEN_ENDPOINT_AUTH_METHODS:
                raise NotImplementedError(
                    "Supported OAuth2 endpoint auth method values: "
                    f"{', '.join(TOKEN_ENDPOINT_AUTH_METHODS)}"
                )

        return SecurityConfig(
            type="oauth2",
            values=security_values,
            flow=flow_type,
            token_url=_required_string(
                flow.get("tokenUrl"),
                "OAuth2 tokenUrl",
            ),
            scope=_format_oauth_scopes(flow.get("scopes")),
            token_endpoint_auth_method=cast(
                TokenEndpointAuthMethod,
                token_auth_method,
            ),
            token_cache=token_cache,
        )

    if scheme_type == "http":
        scheme = _required_string(
            security_scheme.get("scheme"),
            "HTTP auth scheme",
        ).lower()

        if scheme not in HTTP_AUTH_SCHEMES:
            raise NotImplementedError(
                f"Supported HTTP auth scheme values: {', '.join(HTTP_AUTH_SCHEMES)}"
            )

        return SecurityConfig(
            type="http",
            values=security_values,
            scheme=cast(
                HttpAuthScheme,
                scheme,
            ),
        )

    if scheme_type == "apiKey":
        location = security_scheme.get("in")

        if location not in SECURITY_LOCATIONS:
            raise ValueError(
                f"Supported API key locations: {', '.join(SECURITY_LOCATIONS)}"
            )

        return SecurityConfig(
            type="apiKey",
            values=security_values,
            location=cast(
                SecurityLocation,
                location,
            ),
            name=_required_string(
                security_scheme.get("name"),
                "API key name",
            ),
        )

    raise NotImplementedError(f"Unsupported security scheme type: {scheme_type}")


def token_cache_cfg_from_openapi(
    cache_key: str,
    security_scheme: Mapping[str, Any],
    *,
    extension_name: str = "tokenCache",
) -> TokenCacheConfig | None:
    """Build token cache configuration from the OpenAPI extension."""
    if cache_key is None or security_scheme is None:
        return None

    extension = security_scheme.get(extension_name)

    if extension is None:
        return None

    if not isinstance(extension, Mapping):
        raise ValueError("extension must be an object")

    enabled = extension.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("extension.enabled must be a boolean")

    expiry_skew = extension.get("expirySkew", 60)
    if (
        isinstance(expiry_skew, bool)
        or not isinstance(expiry_skew, (int, float))
        or expiry_skew < 0
    ):
        raise ValueError("extension.expirySkew must be a non-negative number")

    expires_in = extension.get("expiresIn")
    if expires_in is not None and (
        isinstance(expires_in, bool)
        or not isinstance(expires_in, (int, float))
        or expires_in <= 0
    ):
        raise ValueError("extension.expiresIn must be a positive number")

    return TokenCacheConfig(
        enabled=enabled,
        expiry_skew=float(expiry_skew),
        expires_in=(None if expires_in is None else float(expires_in)),
        key=cache_key,
    )
