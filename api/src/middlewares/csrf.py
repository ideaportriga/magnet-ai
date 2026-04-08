"""
CSRF protection middleware — Origin/Referer validation for cookie-authenticated requests.

This provides defense-in-depth alongside SameSite=Lax cookies.
Only applies to state-changing methods (POST, PUT, DELETE, PATCH)
when the request uses cookie-based authentication.
"""

from __future__ import annotations

from logging import getLogger
from urllib.parse import urlparse

from litestar.connection import ASGIConnection
from litestar.enums import ScopeType
from litestar.exceptions import PermissionDeniedException
from litestar.middleware import AbstractMiddleware
from litestar.types import Receive, Scope, Send

from core.config.base import get_auth_settings

logger = getLogger(__name__)

# Safe HTTP methods that don't modify state
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _get_allowed_origins() -> set[str]:
    """Build set of allowed origins from configuration."""
    import os


    settings = get_auth_settings()
    origins = set()

    # The main app URL
    base_url = settings.OAUTH2_REDIRECT_BASE_URL
    if base_url:
        parsed = urlparse(base_url)
        origins.add(f"{parsed.scheme}://{parsed.netloc}")

    # Also allow the redirect URI origin
    redirect_uri = settings.MICROSOFT_ENTRA_ID_REDIRECT_URI
    if redirect_uri:
        parsed = urlparse(redirect_uri)
        origins.add(f"{parsed.scheme}://{parsed.netloc}")

    # Include CORS allowed origins so cookie-auth requests from the
    # frontend dev server are not blocked by CSRF validation.
    cors_raw = os.environ.get("CORS_OVERRIDE_ALLOWED_ORIGINS", "")
    for origin in cors_raw.split(","):
        origin = origin.strip()
        if origin:
            origins.add(origin)

    return origins


class CSRFMiddleware(AbstractMiddleware):
    """Validate Origin/Referer for state-changing cookie-auth requests.

    Checks:
    1. Skip safe methods (GET, HEAD, OPTIONS)
    2. Skip API key auth (uses header, not cookies)
    3. Skip if no auth cookies present (unauthenticated or Bearer auth)
    4. For cookie-auth POST/PUT/DELETE/PATCH: validate Origin or Referer header
    """

    scopes = {ScopeType.HTTP}
    exclude_opt_key = "exclude_from_csrf"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        connection = ASGIConnection(scope)
        method = scope.get("method", "GET")

        # 1. Safe methods — skip
        if method in SAFE_METHODS:
            await self.app(scope, receive, send)
            return

        # 2. No auth cookies — not a cookie-based session, skip
        if not connection.cookies.get("token"):
            await self.app(scope, receive, send)
            return

        # 3. API key header present — not cookie auth, skip
        if connection.headers.get("x-api-key"):
            await self.app(scope, receive, send)
            return

        # 4. Validate Origin or Referer
        origin = connection.headers.get("origin")
        referer = connection.headers.get("referer")

        if origin:
            request_origin = origin
        elif referer:
            parsed = urlparse(referer)
            request_origin = f"{parsed.scheme}://{parsed.netloc}"
        else:
            # No Origin or Referer — block
            logger.warning(
                "CSRF: Blocked %s request to %s — missing Origin/Referer",
                method,
                scope.get("path", "?"),
            )
            raise PermissionDeniedException(
                "Missing Origin or Referer header for state-changing request"
            )

        allowed = _get_allowed_origins()
        if request_origin not in allowed:
            logger.warning(
                "CSRF: Blocked %s request to %s — origin %s not in allowed %s",
                method,
                scope.get("path", "?"),
                request_origin,
                allowed,
            )
            raise PermissionDeniedException("Origin not allowed")

        await self.app(scope, receive, send)
