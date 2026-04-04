"""Unified cookie helpers for authentication tokens.

All auth cookies should use these helpers to ensure consistent security
attributes (HttpOnly, Secure, SameSite, Partitioned) across the application.
"""

from __future__ import annotations

from litestar.response import Response

from core.config.base import get_auth_settings


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
        secure=True,
        samesite="none",
        path="/",
        max_age=token_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=refresh_max_age,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    response.delete_cookie(key="token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
