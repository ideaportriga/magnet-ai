"""Higher-level router-scoped guards built on top of `guards.permissions`.

These exist so the `/api/admin/*` router has a soft "must be a logged-in
principal with at least one permission" check while the actual per-endpoint
authorization stays explicit (`require_permission(...)`). Without this the
old router-level `create_role_guard(UserRole.ADMIN)` would block users who
have a custom or non-admin role but legitimate access to specific
endpoints (e.g. a `viewer` doing `GET /admin/agents`).
"""

from __future__ import annotations

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

from core.config.base import get_auth_settings
from guards.permissions import get_effective_permissions


def require_any_admin_capability() -> Guard:
    """Pass any authenticated principal that has at least one permission.

    Per-endpoint guards (`require_permission(Permission.AGENTS_READ)`, etc.)
    are the real gate. This router-level check just keeps the admin surface
    from leaking 401-vs-403 oracles to unauthenticated noise.
    """

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        auth = connection.scope.get("auth")
        if not auth:
            if not get_auth_settings().AUTH_ENABLED:
                return
            raise PermissionDeniedException("Authentication required.")

        # Platform superuser short-circuits.
        user = getattr(auth, "user", None)
        if user is not None and getattr(user, "is_superuser", False):
            return

        if not get_effective_permissions(auth):
            raise PermissionDeniedException(
                "No permissions assigned for the current principal."
            )

    return guard
