"""
Scope-based access control guard for API keys.

Usage:
    @post("/api/datasets", guards=[require_scope("write:datasets")])
"""

from __future__ import annotations

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

from middlewares.auth import Auth


def require_scope(*required_scopes: str) -> Guard:
    """Create a guard that checks if the API key has at least one of the required scopes.

    Only applies to API key auth. Session-based auth (JWT) is not scoped
    and passes through (use role guards for session auth).
    """
    scope_set = set(required_scopes)

    def scope_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        auth: Auth | None = connection.scope.get("auth")
        if not auth:
            raise PermissionDeniedException("Authentication required.")

        # Only enforce scopes for API key auth
        if auth.type != "api_key":
            return

        key_scopes = auth.data.get("scopes")
        if key_scopes is None:
            # Legacy key without scopes — allow (backward compat, gets 'user' role)
            return

        if not (set(key_scopes) & scope_set):
            raise PermissionDeniedException(
                f"API key missing required scope: {', '.join(scope_set)}"
            )

    return scope_guard
