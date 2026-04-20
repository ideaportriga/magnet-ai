"""
Generic OIDC identity strategy.

Works with any OIDC-compliant provider: Microsoft Entra ID, Google, Okta,
Auth0, Keycloak, Zitadel, Oracle, etc. Configuration is data, not code.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from logging import getLogger
from typing import Any
from urllib.parse import urlencode

import httpx
from cachetools import TTLCache
from jose import jwt

from services.auth.types import ExternalIdentity

logger = getLogger(__name__)

# OIDC discovery documents change rarely; JWKS keys rotate on provider-set
# schedules (typically hours/days). Previous impl used a bare dict → no
# refresh across the lifetime of the process, so key rotation at the IdP
# required an app restart. TTLCache gives us stale-while-revalidate below.
# See BACKEND_FIXES_ROADMAP.md §C.3.
_DISCOVERY_TTL_SECONDS = 3600  # 1 hour
_JWKS_TTL_SECONDS = 600  # 10 minutes
_CACHE_MAXSIZE = 64

_discovery_cache: TTLCache[str, dict] = TTLCache(
    maxsize=_CACHE_MAXSIZE, ttl=_DISCOVERY_TTL_SECONDS
)
_jwks_cache: TTLCache[str, dict] = TTLCache(
    maxsize=_CACHE_MAXSIZE, ttl=_JWKS_TTL_SECONDS
)

# Keeps last-known-good values even after TTL expiry — used when the IdP is
# transiently unavailable so auth still works (read-only dict semantics).
_discovery_stale: dict[str, dict] = {}
_jwks_stale: dict[str, dict] = {}
_discovery_fetched_at: dict[str, float] = {}
_jwks_fetched_at: dict[str, float] = {}

# Per-URL locks so we don't thunder-herd the IdP with N concurrent refreshes
# when the cache expires under load.
_discovery_locks: dict[str, asyncio.Lock] = {}
_jwks_locks: dict[str, asyncio.Lock] = {}


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


def _lock_for(url: str, bucket: dict[str, asyncio.Lock]) -> asyncio.Lock:
    lock = bucket.get(url)
    if lock is None:
        lock = asyncio.Lock()
        bucket[url] = lock
    return lock


async def _fetch_with_ttl(
    url: str,
    *,
    cache: TTLCache,
    stale: dict[str, dict],
    fetched_at: dict[str, float],
    locks: dict[str, asyncio.Lock],
    label: str,
) -> dict:
    """TTL-cached HTTP GET with stale-while-revalidate fallback.

    * Cache hit → return cached value.
    * Miss under lock → fetch, cache, and remember as last-known-good.
    * Miss + IdP error → serve last-known-good with a warning rather than
      hard-failing every login during a transient outage.
    """
    hit = cache.get(url)
    if hit is not None:
        return hit

    async with _lock_for(url, locks):
        hit = cache.get(url)
        if hit is not None:
            return hit

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status()
                doc = resp.json()
        except Exception as exc:
            last_known = stale.get(url)
            if last_known is not None:
                age = time.monotonic() - fetched_at.get(url, 0.0)
                logger.warning(
                    "OIDC %s fetch failed for %s (%s); serving stale copy (%.0fs old)",
                    label,
                    url,
                    exc,
                    age,
                )
                return last_known
            raise

        cache[url] = doc
        stale[url] = doc
        fetched_at[url] = time.monotonic()
        return doc


async def _fetch_discovery(discovery_url: str) -> dict:
    """Fetch and TTL-cache OIDC discovery document."""
    return await _fetch_with_ttl(
        discovery_url,
        cache=_discovery_cache,
        stale=_discovery_stale,
        fetched_at=_discovery_fetched_at,
        locks=_discovery_locks,
        label="discovery",
    )


async def _fetch_jwks(jwks_uri: str) -> dict:
    """Fetch and TTL-cache JWKS keys."""
    return await _fetch_with_ttl(
        jwks_uri,
        cache=_jwks_cache,
        stale=_jwks_stale,
        fetched_at=_jwks_fetched_at,
        locks=_jwks_locks,
        label="jwks",
    )


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
