"""Startup plugin for handling application initialization."""

import asyncio
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

        # Install a global asyncio exception handler so background tasks that
        # die without anyone awaiting them still produce a log line. Without
        # this, an unhandled exception in a fire-and-forget asyncio.create_task
        # can disappear silently — which is one of the root causes of the
        # "long-running extraction stopped without any log" bug.
        self._install_asyncio_exception_handler()

        # Register LiteLLM callback logger for observability
        self._register_litellm_callbacks()

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

        # Preload Teams note-taker bot if configured via environment
        await self._initialize_teams_note_taker_runtime(app)

        # Load additional note-taker runtimes from DB provider references
        await self._initialize_note_taker_registry(app)

        # Reconcile stale 'running' extraction state in DB. The previous
        # process may have crashed / been SIGKILL'd while an extraction was
        # in flight, leaving the graph's state forever stuck on 'running'.
        await self._reconcile_stale_extractions()

    @staticmethod
    def _install_asyncio_exception_handler() -> None:
        """Catch-all logging for exceptions raised in detached asyncio tasks."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning(
                "No running event loop at startup; "
                "asyncio exception handler not installed"
            )
            return

        def _handler(_loop, context):
            message = context.get("message") or "asyncio unhandled exception"
            exc = context.get("exception")
            task = context.get("task")
            task_name = task.get_name() if task is not None else None
            if exc is not None:
                logger.error(
                    "asyncio loop error: %s (task=%s)",
                    message,
                    task_name,
                    exc_info=exc,
                )
            else:
                logger.error(
                    "asyncio loop error: %s (task=%s, context=%r)",
                    message,
                    task_name,
                    context,
                )

        loop.set_exception_handler(_handler)
        logger.info("Global asyncio exception handler installed")

    @staticmethod
    def _register_litellm_callbacks() -> None:
        """Register LiteLLM callback logger for failure/success observability."""
        try:
            import litellm

            from services.ai_services.callbacks import MagnetAILogger

            litellm.callbacks.append(MagnetAILogger())
            logger.info("LiteLLM callback logger registered")
        except Exception as e:
            logger.warning("Failed to register LiteLLM callbacks: %s", e)

    async def _initialize_scheduler(self, app: Litestar) -> None:
        """Initialize the scheduler."""
        try:
            from scheduler import create_scheduler

            scheduler = await create_scheduler()
            app.state.scheduler = scheduler
            logger.info("Scheduler started successfully")

            # Register periodic cleanup of temporary uploaded files
            self._register_upload_cleanup_job(scheduler)
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            # Set scheduler to None so we can handle it in shutdown
            app.state.scheduler = None
            # Don't raise the exception to allow the app to start without scheduler

    @staticmethod
    def _register_upload_cleanup_job(scheduler) -> None:
        """Register a periodic job that removes expired knowledge-source uploads."""
        try:
            from apscheduler.triggers.interval import IntervalTrigger

            from services.file_cleanup import (
                KS_UPLOAD_CLEANUP_INTERVAL_MINUTES,
                cleanup_old_uploads,
            )

            job_id = "ks_upload_cleanup"

            # Remove stale job definition if it already exists (e.g. after restart)
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)

            scheduler.add_job(
                cleanup_old_uploads,
                trigger=IntervalTrigger(minutes=KS_UPLOAD_CLEANUP_INTERVAL_MINUTES),
                id=job_id,
                name="Cleanup expired knowledge-source uploads",
                replace_existing=True,
            )
            logger.info(
                "Registered ks_upload_cleanup job (every %d min)",
                KS_UPLOAD_CLEANUP_INTERVAL_MINUTES,
            )
        except Exception as e:
            logger.warning("Failed to register upload cleanup job: %s", e)

        # Register TTL cleanup for expired note-taker pending confirmations
        try:
            from apscheduler.triggers.interval import IntervalTrigger
            from services.agents.teams.note_taker_pending_store import cleanup_expired

            pending_job_id = "note_taker_pending_cleanup"
            if scheduler.get_job(pending_job_id):
                scheduler.remove_job(pending_job_id)

            scheduler.add_job(
                cleanup_expired,
                trigger=IntervalTrigger(hours=1),
                id=pending_job_id,
                name="Cleanup expired note-taker speaker-mapping confirmations",
                replace_existing=True,
            )
            logger.info("Registered note_taker_pending_cleanup job (every 1h)")
        except Exception as e:
            logger.warning("Failed to register note_taker_pending_cleanup job: %s", e)

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

    async def _initialize_teams_note_taker_runtime(self, app: Litestar) -> None:
        """Initialize the Teams note-taker bot from environment variables, if available."""
        try:
            from services.agents.teams.note_taker import (
                load_note_taker_runtime_from_env,
            )

            runtime = load_note_taker_runtime_from_env()
            if runtime is None:
                logger.info(
                    "Teams note-taker env vars not set; skipping bot initialization."
                )
                return

            app.state.teams_note_taker_runtime = runtime
            logger.info("Teams note-taker runtime initialized.")
        except Exception as exc:
            logger.exception("Failed to initialize Teams note-taker runtime: %s", exc)

    @staticmethod
    async def _reconcile_stale_extractions() -> None:
        """Mark orphan 'running'/'syncing' KG state as 'interrupted' on startup."""
        try:
            from services.knowledge_graph.llm_entity_extraction import (
                reconcile_stale_entity_extractions,
            )
            from services.knowledge_graph.llm_metadata_extraction import (
                reconcile_stale_metadata_extractions,
            )
            from services.knowledge_graph.sources.sync_services import (
                reconcile_stale_source_syncs,
            )

            entity_updated = await reconcile_stale_entity_extractions()
            metadata_updated = await reconcile_stale_metadata_extractions()
            sync_updated = await reconcile_stale_source_syncs()
            logger.info(
                "Startup reconciliation: entity=%d, metadata=%d, sync=%d row(s) marked interrupted",
                entity_updated,
                metadata_updated,
                sync_updated,
            )
        except Exception as exc:
            logger.exception("Failed to reconcile stale extractions: %s", exc)

    async def _initialize_note_taker_registry(self, app: Litestar) -> None:
        """Load all note-taker runtimes from DB records that reference a Provider."""
        try:
            from services.agents.teams.note_taker import NoteTakerRegistry

            registry = NoteTakerRegistry()
            loaded = await registry.load_all_from_db()
            app.state.note_taker_registry = registry
            logger.info(
                "NoteTakerRegistry initialized with %d runtime(s) from DB.", loaded
            )
        except Exception as exc:
            logger.exception("Failed to initialize NoteTakerRegistry: %s", exc)
