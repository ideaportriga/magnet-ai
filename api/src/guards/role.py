from enum import StrEnum

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

from middlewares.auth import Auth


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


# Default role slug assigned to new users on first OIDC login
DEFAULT_ROLE_SLUG = "user"

# Superuser role slug (full access)
SUPERUSER_ROLE_SLUG = "admin"


def create_role_guard(*required_roles: str | UserRole) -> Guard:
    """Create a guard that checks if the user has at least one of the required roles.

    Checks in order:
    1. If user has a DB User object with roles loaded → check role slugs from DB
    2. Fallback to auth.data["roles"] from OIDC token / API key (backward compat)

    Args:
        *required_roles: One or more role slugs that grant access.
    """
    role_set = {str(r) for r in required_roles}

    def role_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        auth: Auth | None = connection.scope.get("auth")

        if not auth:
            raise PermissionDeniedException("Authentication required.")

        # Check DB roles first (if User object is available from Phase 1 middleware)
        user = getattr(auth, "user", None)
        if user is not None:
            # user.roles is a list of Role objects (selectin-loaded)
            user_role_slugs = {r.slug for r in (user.roles or [])}
            # Superusers bypass role checks
            if user.is_superuser:
                return
            if user_role_slugs & role_set:
                return
            raise PermissionDeniedException(
                f"Requires one of roles: {', '.join(role_set)}"
            )

        # Fallback: check roles from token/API key data (backward compat)
        token_roles = auth.data.get("roles", set())
        if isinstance(token_roles, list):
            token_roles = set(token_roles)

        if token_roles & role_set:
            return

        raise PermissionDeniedException(f"Requires one of roles: {', '.join(role_set)}")

    return role_guard
