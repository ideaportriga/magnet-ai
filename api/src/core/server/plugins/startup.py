"""Startup plugin for handling application initialization."""

import os
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Litestar
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


class StartupPlugin(InitPluginProtocol):
    """Plugin to handle application startup logic."""

    def __init__(self) -> None:
        self.env = os.environ
        self.db_type = self.env.get("VECTOR_DB_TYPE")
        self.auth_enabled = self.env.get("AUTH_ENABLED") == "true"

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure app startup handlers."""
        startup_handlers = list(app_config.on_startup or [])
        startup_handlers.append(self._on_startup)
        app_config.on_startup = startup_handlers
        return app_config

    async def _on_startup(self, app: Litestar) -> None:
        """Application startup handler."""
        logger.info("Starting application...")

        # Initialize scheduler
        await self._initialize_scheduler(app)

        # Refresh API keys cache if auth is enabled
        if self.auth_enabled:
            await self._refresh_api_keys()

        # Initialize database connections
        await self._initialize_database_connections()

        logger.info("SQLAlchemy engine initialized via plugin")

        # Preload Slack runtimes
        await self._initialize_slack_runtime_cache(app)

    async def _initialize_scheduler(self, app: Litestar) -> None:
        """Initialize the scheduler."""
        try:
            from scheduler import create_scheduler

            scheduler = await create_scheduler()
            app.state.scheduler = scheduler
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            # Set scheduler to None so we can handle it in shutdown
            app.state.scheduler = None
            # Don't raise the exception to allow the app to start without scheduler

    async def _refresh_api_keys(self) -> None:
        """Refresh API keys cache."""
        try:
            from services.api_keys.services import refresh_api_keys_caches

            await refresh_api_keys_caches()
            logger.info("API keys cache refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh API keys cache: {e}")

    async def _initialize_database_connections(self) -> None:
        """Initialize database connection pools based on VECTOR_DB_TYPE."""
        if self.db_type == "PGVECTOR":
            await self._initialize_pgvector()

    async def _initialize_pgvector(self) -> None:
        """Initialize PgVector connection pool."""
        logger.info("Initializing PgVector connection pool...")
        try:
            from stores.pgvector_db import pgvector_client

            logger.info("PgVector client imported successfully")
            await pgvector_client.init_pool()
            await pgvector_client.ensure_pgvector_extension()
            logger.info("PgVector connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PgVector connection pool: {e}")
            raise

    async def _initialize_slack_runtime_cache(self, app: Litestar) -> None:
        """Initialize Slack runtime"""
        try:
            from services.agents.slack.runtime_cache import SlackRuntimeCache

            cache = SlackRuntimeCache()
            app.state.slack_runtime_cache = cache
            await cache.load()
            logger.info("Slack runtime cache initialized with %d bot(s)", cache.count)
        except Exception as exc:
            logger.exception("Failed to initialize Slack runtime cache: %s", exc)
