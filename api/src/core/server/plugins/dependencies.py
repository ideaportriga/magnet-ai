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

        # SAQ task_queues dependency is automatically registered by SAQPlugin

        # Add user_id dependency
        dependencies["user_id"] = Provide(self._get_user_id)

        app_config.dependencies = dependencies
        return app_config

    async def _get_user_id(self, request: Request) -> str | None:
        """Get user ID from request scope."""
        return request.scope.get("user_id")

    async def _get_db_session(self, request: Request) -> AsyncSession:
        """Get database session from request state."""
        return request.state.db_session
