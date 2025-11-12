"""Middleware configuration plugin."""

import os
from typing import TYPE_CHECKING

from litestar.plugins import InitPluginProtocol
from litestar.types import Middleware

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class MiddlewarePlugin(InitPluginProtocol):
    """Plugin to configure application middleware."""

    def __init__(self) -> None:
        self.env = os.environ
        self.auth_enabled = self.env.get("AUTH_ENABLED") == "true"
        self.auth_enabled_for_schema = self.env.get("AUTH_ENABLED_FOR_SCHEMA") == "true"

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure middleware stack."""
        middlewares: list[Middleware] = []

        # Add database error logging middleware
        try:
            from middlewares.database_error import DatabaseErrorLoggingMiddleware

            middlewares.append(DatabaseErrorLoggingMiddleware)
        except ImportError:
            pass

        # Add auth middleware if enabled
        if self.auth_enabled:
            try:
                from middlewares.auth import create_auth_middleware

                exclude_param = None if self.auth_enabled_for_schema else "schema"
                middlewares.append(create_auth_middleware(exclude_param=exclude_param))
            except ImportError:
                pass

        # Combine with existing middleware
        existing_middleware = list(app_config.middleware or [])
        app_config.middleware = existing_middleware + middlewares

        return app_config
