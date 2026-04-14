"""
Generic OIDC identity strategy.

Works with any OIDC-compliant provider: Microsoft Entra ID, Google, Okta,
Auth0, Keycloak, Zitadel, Oracle, etc. Configuration is data, not code.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import jwt

from services.auth.types import ExternalIdentity

logger = getLogger(__name__)


@dataclass
class OIDCProviderConfig:
    """Configuration for a single OIDC provider."""

    name: str  # 'microsoft', 'google', 'corporate-sso'
    discovery_url: str  # .well-known/openid-configuration URL
    client_id: str
    client_secret: str
    redirect_uri: str  # callback URL on our side
    scopes: list[str] | None = None  # default: openid profile email
    # Override auto-discovered endpoints (for providers with non-standard URLs)
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    jwks_uri: str | None = None
    userinfo_endpoint: str | None = None
    # Provider-specific options
    audience: str | None = None  # for token validation (defaults to client_id)
    user_id_claim: str = "sub"  # claim for unique user ID
    response_mode: str = "query"  # 'query', 'form_post'
    response_type: str = "code"


# In-memory caches (populated on first use, cleared on process restart)
_discovery_cache: dict[str, dict] = {}
_jwks_cache: dict[str, dict] = {}


async def _fetch_discovery(discovery_url: str) -> dict:
    """Fetch and cache OIDC discovery document."""
    if discovery_url in _discovery_cache:
        return _discovery_cache[discovery_url]

    async with httpx.AsyncClient() as client:
        resp = await client.get(discovery_url, timeout=10)
        resp.raise_for_status()
        doc = resp.json()
        _discovery_cache[discovery_url] = doc
        return doc


async def _fetch_jwks(jwks_uri: str) -> dict:
    """Fetch and cache JWKS keys."""
    if jwks_uri in _jwks_cache:
        return _jwks_cache[jwks_uri]

    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_uri, timeout=10)
        resp.raise_for_status()
        keys = resp.json()
        _jwks_cache[jwks_uri] = keys
        return keys


class OIDCStrategy:
    """Generic OIDC strategy. Works with any OIDC-compliant provider.

    This is the same strategy used for direct providers (Microsoft, Google)
    and external brokers (Keycloak, Zitadel). The broker is just another
    OIDC provider — no special code path needed.
    """

    def __init__(self, config: OIDCProviderConfig) -> None:
        self.config = config

    def get_provider_name(self) -> str:
        return self.config.name

    async def _get_endpoints(self) -> dict:
        """Resolve OIDC endpoints from discovery or config overrides."""
        discovery = await _fetch_discovery(self.config.discovery_url)
        return {
            "authorization_endpoint": self.config.authorization_endpoint
            or discovery["authorization_endpoint"],
            "token_endpoint": self.config.token_endpoint or discovery["token_endpoint"],
            "jwks_uri": self.config.jwks_uri or discovery["jwks_uri"],
            "userinfo_endpoint": self.config.userinfo_endpoint
            or discovery.get("userinfo_endpoint"),
        }

    async def get_authorization_url(self, state: str, nonce: str) -> str:
        """Build the authorization URL for redirect."""
        endpoints = await self._get_endpoints()
        scopes = self.config.scopes or ["openid", "profile", "email"]

        params = {
            "response_type": self.config.response_type,
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "nonce": nonce,
        }
        if self.config.response_mode != "query":
            params["response_mode"] = self.config.response_mode

        return f"{endpoints['authorization_endpoint']}?{urlencode(params)}"

    async def handle_callback(
        self, request_data: dict[str, Any], expected_nonce: str | None = None
    ) -> ExternalIdentity:
        """Exchange authorization code for tokens and extract identity."""
        code = request_data.get("code")
        if not code:
            raise ValueError("Missing authorization code in callback")

        endpoints = await self._get_endpoints()

        # Exchange code for tokens
        token_data = await self._exchange_code(code, endpoints["token_endpoint"])

        # Only use id_token for identity — access_token is not an identity assertion
        id_token = token_data.get("id_token")
        if not id_token:
            raise ValueError(
                "No id_token in token response — provider may not support OIDC"
            )

        # Validate and decode the token
        jwks = await _fetch_jwks(endpoints["jwks_uri"])
        audience = self.config.audience or self.config.client_id
        claims = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=audience,
            options={
                "verify_exp": True,
                "verify_aud": True,
                "verify_at_hash": False,
            },
        )

        # Validate nonce
        if expected_nonce:
            token_nonce = claims.get("nonce")
            if not token_nonce:
                raise ValueError("Token missing nonce claim")
            if token_nonce != expected_nonce:
                raise ValueError("Nonce mismatch")

        # Extract identity
        subject_id = str(claims.get(self.config.user_id_claim, ""))
        email = claims.get("email") or claims.get("preferred_username", "")
        name = claims.get("name")
        email_verified = claims.get("email_verified", False)

        # Some providers (Microsoft) put roles in claims
        suggested_roles = claims.get("roles")
        if isinstance(suggested_roles, str):
            suggested_roles = [suggested_roles]

        return ExternalIdentity(
            provider=self.config.name,
            subject_id=subject_id,
            email=email,
            name=name,
            email_verified=bool(email_verified),
            raw_claims=claims,
            suggested_roles=suggested_roles,
        )

    async def _exchange_code(self, code: str, token_endpoint: str) -> dict:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(token_endpoint, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
