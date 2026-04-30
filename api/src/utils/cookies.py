"""Unified cookie helpers for authentication tokens.

All cookies use SameSite=Lax. In dev, Vite proxy ensures same-origin.
In production, nginx serves everything on the same domain.
"""

from __future__ import annotations

from typing import Literal, cast

from litestar.response import Response
from litestar.response.base import ASGIResponse

from core.config.base import get_auth_settings

CookieSameSite = Literal["lax", "strict", "none"]


def _cookie_samesite() -> CookieSameSite:
    settings = get_auth_settings()
    value = settings.AUTH_COOKIE_SAMESITE.lower()
    if value in {"lax", "strict", "none"}:
        return cast(CookieSameSite, value)
    return "lax"


def _cookie_domain() -> str | None:
    settings = get_auth_settings()
    return settings.AUTH_COOKIE_DOMAIN or None


def _set_cookie_secure() -> bool:
    settings = get_auth_settings()
    return settings.AUTH_COOKIE_SECURE


def validate_cookie_settings() -> None:
    """Reject incompatible auth cookie configurations at startup.

    Browsers silently drop SameSite=None cookies that are not also Secure,
    which would manifest as broken refresh with no client-side error.
    """
    settings = get_auth_settings()
    if (
        settings.AUTH_COOKIE_SAMESITE.lower() == "none"
        and not settings.AUTH_COOKIE_SECURE
    ):
        raise ValueError(
            "AUTH_COOKIE_SAMESITE=none requires AUTH_COOKIE_SECURE=true; "
            "browsers will drop the cookie otherwise."
        )


_MIN_SECRET_KEY_LENGTH = 32


def validate_auth_settings() -> None:
    """Validate the full auth configuration at startup.

    Fails fast on misconfigurations that would otherwise produce silently
    broken auth (empty secrets accepted, wrong cookie flags, encryption
    key reused for signing, etc.).
    """
    settings = get_auth_settings()

    if not settings.AUTH_ENABLED:
        return

    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH:
        raise ValueError(
            f"SECRET_KEY must be at least {_MIN_SECRET_KEY_LENGTH} chars when "
            "AUTH_ENABLED=true (used to sign internal JWTs)."
        )

    # Cross-purpose key reuse — signing must not equal encryption-at-rest.
    import os

    encryption_key = os.environ.get("SECRET_ENCRYPTION_KEY", "")
    if encryption_key and settings.SECRET_KEY == encryption_key:
        raise ValueError(
            "SECRET_KEY must differ from SECRET_ENCRYPTION_KEY — using one "
            "key for both JWT signing and at-rest encryption breaks the "
            "trust boundary between them."
        )

    validate_cookie_settings()


def _cookie_header(key: str, value: str, max_age: int, path: str = "/") -> str:
    settings = get_auth_settings()
    parts = [f"{key}={value}", f"Max-Age={max_age}"]
    if settings.AUTH_COOKIE_SECURE:
        parts.append("Secure")
    parts.extend(["HttpOnly", f"Path={path}"])
    if settings.AUTH_COOKIE_DOMAIN:
        parts.append(f"Domain={settings.AUTH_COOKIE_DOMAIN}")
    parts.append(f"SameSite={_cookie_samesite().capitalize()}")
    return "; ".join(parts) + ";"


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    """Set both access-token and refresh-token cookies with consistent security attributes."""
    settings = get_auth_settings()
    token_max_age = settings.ACCESS_TOKEN_EXPIRATION_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRATION_DAYS * 86400

    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=_set_cookie_secure(),
        samesite=_cookie_samesite(),
        path="/",
        domain=_cookie_domain(),
        max_age=token_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_set_cookie_secure(),
        samesite=_cookie_samesite(),
        path="/",
        domain=_cookie_domain(),
        max_age=refresh_max_age,
    )


def set_auth_cookies_asgi(
    asgi_response: ASGIResponse,
    access_token: str,
    refresh_token: str,
) -> None:
    """Set auth cookies on an ASGIResponse (for redirect flows)."""
    settings = get_auth_settings()
    token_max_age = settings.ACCESS_TOKEN_EXPIRATION_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRATION_DAYS * 86400

    asgi_response.headers.add(
        "Set-Cookie",
        _cookie_header("token", access_token, token_max_age),
    )
    asgi_response.headers.add(
        "Set-Cookie",
        _cookie_header("refresh_token", refresh_token, refresh_max_age),
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    domain = _cookie_domain()
    response.delete_cookie(key="token", path="/", domain=domain)
    response.delete_cookie(key="refresh_token", path="/", domain=domain)
