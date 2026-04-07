"""
Provider registry — builds identity strategies from configuration.

Providers are configured via environment variables. Adding a new OIDC provider
(including an external broker) is a configuration change, not a code change.
"""

from __future__ import annotations

from logging import getLogger

from core.config.base import get_auth_settings
from services.auth.github_strategy import GitHubStrategy
from services.auth.oidc_strategy import OIDCProviderConfig, OIDCStrategy
from services.auth.types import IdentityStrategy

logger = getLogger(__name__)

# Singleton registry
_providers: dict[str, IdentityStrategy] | None = None


def get_providers() -> dict[str, IdentityStrategy]:
    """Get all configured identity strategy providers.

    Returns a dict of provider_name → IdentityStrategy.
    """
    global _providers
    if _providers is not None:
        return _providers

    _providers = {}
    settings = get_auth_settings()

    # Microsoft Entra ID (OIDC)
    if settings.MICROSOFT_ENTRA_ID_CLIENT_ID and settings.MICROSOFT_ENTRA_ID_TENANT_ID:
        tenant = settings.MICROSOFT_ENTRA_ID_TENANT_ID
        _providers["microsoft"] = OIDCStrategy(
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
        )
        logger.info("Registered OIDC provider: microsoft")

    # Google (OIDC)
    if settings.GOOGLE_OAUTH2_CLIENT_ID:
        _providers["google"] = OIDCStrategy(
            OIDCProviderConfig(
                name="google",
                discovery_url="https://accounts.google.com/.well-known/openid-configuration",
                client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                redirect_uri=f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/v2/auth/sso/google/callback",
                scopes=["openid", "profile", "email"],
            )
        )
        logger.info("Registered OIDC provider: google")

    # GitHub (OAuth2, not fully OIDC)
    if settings.GITHUB_OAUTH2_CLIENT_ID:
        _providers["github"] = GitHubStrategy(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
            redirect_uri=f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/v2/auth/sso/github/callback",
        )
        logger.info("Registered OAuth provider: github")

    return _providers


def get_provider(name: str) -> IdentityStrategy:
    """Get a specific provider by name.

    Raises KeyError if provider is not configured.
    """
    providers = get_providers()
    if name not in providers:
        raise KeyError(f"Unknown or unconfigured auth provider: {name}")
    return providers[name]


def get_provider_names() -> list[str]:
    """Get list of enabled provider names (for /providers endpoint)."""
    return list(get_providers().keys())
