from enum import StrEnum

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

from middlewares.auth import Auth


class UserRole(StrEnum):
    ADMIN = "admin"


def create_role_guard(required_role: UserRole) -> Guard:
    def role_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        auth: Auth = connection.scope.get("auth")

        if not auth:
            raise PermissionDeniedException("Authentication required.")

        user_roles = auth.data.get("roles", [])

        if required_role not in user_roles:
            raise PermissionDeniedException(f"Requires role: {required_role}")

    return role_guard
