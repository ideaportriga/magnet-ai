"""Unified cookie helpers for authentication tokens.

All cookies use SameSite=Lax. In dev, Vite proxy ensures same-origin.
In production, nginx serves everything on the same domain.
"""

from __future__ import annotations

from litestar.response import Response
from litestar.response.base import ASGIResponse

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
        samesite="lax",
        path="/",
        max_age=token_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
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
        f"token={access_token}; Max-Age={token_max_age}; Secure; HttpOnly; Path=/; SameSite=Lax;",
    )
    asgi_response.headers.add(
        "Set-Cookie",
        f"refresh_token={refresh_token}; Max-Age={refresh_max_age}; Secure; HttpOnly; Path=/; SameSite=Lax;",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    response.delete_cookie(key="token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
