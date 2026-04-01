"""Dependencies configuration plugin."""

from typing import TYPE_CHECKING

from litestar import Request
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class DependenciesPlugin(InitPluginProtocol):
    """Plugin to configure application dependencies."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure dependencies."""
        dependencies = dict(app_config.dependencies or {})

        # Add scheduler dependency
        try:
            from scheduler import get_scheduler

            dependencies["scheduler"] = Provide(get_scheduler, sync_to_thread=False)
        except ImportError:
            pass

        # Add user_id dependency
        dependencies["user_id"] = Provide(self._get_user_id)

        # Add preferred_username for audit fields (created_by, updated_by)
        dependencies["audit_username"] = Provide(self._get_audit_username)

        # Add storage dependencies
        dependencies["storage_service"] = Provide(self._get_storage_service)
        dependencies["file_limits"] = Provide(self._get_file_limits)

        app_config.dependencies = dependencies
        return app_config

    async def _get_user_id(self, request: Request) -> str | None:
        """Get user ID from request scope."""
        return request.scope.get("user_id")

    async def _get_audit_username(self, request: Request) -> str | None:
        """Get preferred_username from auth for created_by/updated_by fields."""
        auth = request.scope.get("auth")
        if not auth:
            return None
        return (getattr(auth, "data", None) or {}).get("preferred_username")

    async def _get_db_session(self, request: Request) -> AsyncSession:
        """Get database session from request state."""
        return request.state.db_session

    async def _get_storage_service(self, request: Request):  # noqa: ANN201
        """Get StorageService from app state."""
        return getattr(request.app.state, "storage_service", None)

    async def _get_file_limits(self, request: Request):  # noqa: ANN201
        """Get FileLimits from app state."""
        return getattr(request.app.state, "file_limits", None)
