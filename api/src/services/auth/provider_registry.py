"""
Provider registry — builds identity strategies from configuration.

Providers are configured via environment variables:
- Pre-configured: MICROSOFT_ENTRA_ID_*, GOOGLE_OAUTH2_*, GITHUB_OAUTH2_*
- Generic OIDC:   OIDC_{NAME}_DISCOVERY_URL, OIDC_{NAME}_CLIENT_ID, etc.

AUTH_PROVIDERS env controls which providers are active.
Adding a new OIDC provider is a configuration change, not a code change.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from logging import getLogger

from core.config.base import get_auth_settings
from services.auth.github_strategy import GitHubStrategy
from services.auth.oidc_strategy import OIDCProviderConfig, OIDCStrategy
from services.auth.types import IdentityStrategy

logger = getLogger(__name__)

RESERVED_PROVIDER_NAMES = {"local", "microsoft", "google", "github"}


@dataclass
class ProviderEntry:
    """A registered provider with its strategy and metadata."""

    name: str
    strategy: IdentityStrategy
    provider_type: str  # 'oidc', 'oauth2'
    display_name: str


# Singleton registry
_providers: dict[str, ProviderEntry] | None = None
_allowed_providers: set[str] | None = None


def _has_explicit_provider_allow_list() -> bool:
    """Return True when AUTH_PROVIDERS explicitly lists providers."""
    settings = get_auth_settings()
    return bool(settings.AUTH_PROVIDERS.strip())


def _parse_allowed_providers() -> set[str] | None:
    """Parse AUTH_PROVIDERS env. Returns None if not set (= allow all)."""
    global _allowed_providers
    if _allowed_providers is not None:
        return _allowed_providers

    settings = get_auth_settings()
    raw = settings.AUTH_PROVIDERS.strip()
    if not raw:
        _allowed_providers = set()  # empty = allow all (backward-compatible)
        return _allowed_providers

    _allowed_providers = {p.strip().lower() for p in raw.split(",") if p.strip()}
    return _allowed_providers


def _is_provider_allowed(name: str) -> bool:
    """Check if provider is in the AUTH_PROVIDERS allow-list."""
    allowed = _parse_allowed_providers()
    if not allowed:
        return True  # empty = all allowed
    return name in allowed


def is_local_enabled() -> bool:
    """Check if local (email/password) auth is enabled."""
    allowed = _parse_allowed_providers()
    if not allowed:
        return True  # empty = local included by default
    return "local" in allowed


def _discover_generic_oidc_providers(settings: object) -> dict[str, ProviderEntry]:
    """Scan OIDC_{NAME}_* env vars for generic OIDC provider definitions."""
    providers: dict[str, ProviderEntry] = {}

    # Generic OIDC discovery is opt-in to avoid enabling stray env configs.
    if not _has_explicit_provider_allow_list():
        return providers

    # Find all OIDC_{NAME}_DISCOVERY_URL env vars
    oidc_pattern = re.compile(r"^OIDC_([A-Z][A-Z0-9_]*)_DISCOVERY_URL$")
    for key, discovery_url in os.environ.items():
        match = oidc_pattern.match(key)
        if not match or not discovery_url:
            continue

        name_upper = match.group(1)
        name = name_upper.lower()

        if name in RESERVED_PROVIDER_NAMES:
            logger.warning(
                "OIDC provider %s uses a reserved name and will be ignored",
                name,
            )
            continue

        # Skip if not allowed
        if not _is_provider_allowed(name):
            continue

        prefix = f"OIDC_{name_upper}_"
        client_id = os.getenv(f"{prefix}CLIENT_ID", "")
        client_secret = os.getenv(f"{prefix}CLIENT_SECRET", "")

        if not client_id:
            logger.warning("OIDC provider %s: CLIENT_ID not set, skipping", name)
            continue

        base_url = get_auth_settings().OAUTH2_REDIRECT_BASE_URL
        redirect_uri = os.getenv(
            f"{prefix}REDIRECT_URI",
            f"{base_url}/api/v2/auth/sso/{name}/callback",
        )
        scopes_raw = os.getenv(f"{prefix}SCOPES", "openid,profile,email")
        scopes = [s.strip() for s in scopes_raw.split(",")]
        user_id_claim = os.getenv(f"{prefix}USER_ID_CLAIM", "sub")
        response_mode = os.getenv(f"{prefix}RESPONSE_MODE", "query")
        display_name = os.getenv(
            f"{prefix}DISPLAY_NAME",
            name.replace("_", " ").title(),
        )

        providers[name] = ProviderEntry(
            name=name,
            strategy=OIDCStrategy(
                OIDCProviderConfig(
                    name=name,
                    discovery_url=discovery_url,
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scopes=scopes,
                    user_id_claim=user_id_claim,
                    response_mode=response_mode,
                )
            ),
            provider_type="oidc",
            display_name=display_name,
        )
        logger.info("Registered generic OIDC provider: %s (%s)", name, display_name)

    return providers


def _build_providers() -> dict[str, ProviderEntry]:
    """Build full provider registry from env configuration."""
    providers: dict[str, ProviderEntry] = {}
    settings = get_auth_settings()

    # Microsoft Entra ID (OIDC) — pre-configured
    if (
        settings.MICROSOFT_ENTRA_ID_CLIENT_ID
        and settings.MICROSOFT_ENTRA_ID_TENANT_ID
        and _is_provider_allowed("microsoft")
    ):
        tenant = settings.MICROSOFT_ENTRA_ID_TENANT_ID
        providers["microsoft"] = ProviderEntry(
            name="microsoft",
            strategy=OIDCStrategy(
                OIDCProviderConfig(
                    name="microsoft",
                    discovery_url=f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration",
                    client_id=settings.MICROSOFT_ENTRA_ID_CLIENT_ID,
                    client_secret=settings.MICROSOFT_ENTRA_ID_CLIENT_SECRET,
                    redirect_uri=settings.MICROSOFT_ENTRA_ID_REDIRECT_URI
                    or f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/v2/auth/sso/microsoft/callback",
                    scopes=["openid", "profile", "email", "offline_access"],
                    user_id_claim="oid",
                    response_mode="form_post",
                )
            ),
            provider_type="oidc",
            display_name="Microsoft",
        )
        logger.info("Registered OIDC provider: microsoft")

    # Google (OIDC) — pre-configured
    if settings.GOOGLE_OAUTH2_CLIENT_ID and _is_provider_allowed("google"):
        providers["google"] = ProviderEntry(
            name="google",
            strategy=OIDCStrategy(
                OIDCProviderConfig(
                    name="google",
                    discovery_url="https://accounts.google.com/.well-known/openid-configuration",
                    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    redirect_uri=f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/v2/auth/sso/google/callback",
                    scopes=["openid", "profile", "email"],
                )
            ),
            provider_type="oidc",
            display_name="Google",
        )
        logger.info("Registered OIDC provider: google")

    # GitHub (OAuth2, not fully OIDC) — pre-configured
    if settings.GITHUB_OAUTH2_CLIENT_ID and _is_provider_allowed("github"):
        providers["github"] = ProviderEntry(
            name="github",
            strategy=GitHubStrategy(
                client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
                client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
                redirect_uri=f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/v2/auth/sso/github/callback",
            ),
            provider_type="oauth2",
            display_name="GitHub",
        )
        logger.info("Registered OAuth provider: github")

    # Generic OIDC providers from OIDC_{NAME}_* env vars
    generic = _discover_generic_oidc_providers(settings)
    providers.update(generic)

    return providers


def get_providers() -> dict[str, ProviderEntry]:
    """Get all configured provider entries.

    Returns a dict of provider_name → ProviderEntry.
    """
    global _providers
    if _providers is not None:
        return _providers
    _providers = _build_providers()
    return _providers


def get_provider(name: str) -> IdentityStrategy:
    """Get a specific provider's strategy by name.

    Raises KeyError if provider is not configured.
    """
    providers = get_providers()
    if name not in providers:
        raise KeyError(f"Unknown or unconfigured auth provider: {name}")
    return providers[name].strategy


def get_provider_names() -> list[str]:
    """Get list of enabled provider names (for /providers endpoint)."""
    return list(get_providers().keys())


def get_provider_info() -> list[dict[str, str]]:
    """Get provider metadata for the /providers endpoint.

    Returns list of dicts with name, type, displayName.
    Includes 'local' if email/password auth is enabled.
    """
    result: list[dict[str, str]] = []

    if is_local_enabled():
        result.append({"name": "local", "type": "local", "displayName": "Email"})

    for entry in get_providers().values():
        result.append(
            {
                "name": entry.name,
                "type": entry.provider_type,
                "displayName": entry.display_name,
            }
        )

    return result
