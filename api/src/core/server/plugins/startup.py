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

        # Validate the full auth configuration before serving any requests
        # so that misconfigurations (empty SECRET_KEY, SameSite=None without
        # Secure, signing key reused for encryption, ...) fail loudly rather
        # than silently producing broken auth.
        if self.auth_enabled:
            from utils.cookies import validate_auth_settings

            validate_auth_settings()

        # Optional dev convenience: create/promote a superuser on startup so
        # a fresh `npm run dev` lands you in a usable app without a separate
        # `bootstrap_superuser.py` step. Gated by AUTO_CREATE_SUPERUSER and
        # blocked entirely in production.
        if self.auth_enabled:
            await self._maybe_bootstrap_superuser()

        # Event loop lag monitor — early signal for slow async callbacks
        self._start_event_loop_monitor(app)

        # Register LiteLLM callback logger for observability
        self._register_litellm_callbacks()

        # Start the TaskIQ broker on the API process so `.kiq()` works from
        # route handlers. Worker-side startup is handled by
        # `tasks.worker_lifecycle` via WORKER_STARTUP; this call is API-only.
        await self._startup_taskiq_broker(app)

        # Refresh API keys cache if auth is enabled
        if self.auth_enabled:
            await self._refresh_api_keys()

        # Initialize database connections
        await self._initialize_database_connections()

        logger.info("SQLAlchemy engine initialized via plugin")

        # Initialize unified file storage
        await self._initialize_storage(app)

        # Preload Slack runtimes
        await self._initialize_slack_runtime_cache(app)

        # Preload Teams note-taker bot if configured via environment
        await self._initialize_teams_note_taker_runtime(app)

        # Load additional note-taker runtimes from DB provider references
        await self._initialize_note_taker_registry(app)

    @staticmethod
    def _start_event_loop_monitor(app: Litestar) -> None:
        """Launch the background event-loop-lag monitor (see §B.5)."""
        try:
            from core.server.plugins.event_loop_monitor import start_event_loop_monitor

            app.state.event_loop_monitor_task = start_event_loop_monitor()
            logger.info("Event loop lag monitor started")
        except Exception as e:
            logger.warning("Failed to start event loop lag monitor: %s", e)

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

    @staticmethod
    async def _startup_taskiq_broker(app: Litestar) -> None:
        """Start the TaskIQ broker on the API process.

        In the in-process / single-container layout this is the only place
        the broker is started — `TaskiqRuntimePlugin` later flips
        `broker.is_worker_process=True` and spawns the receiver task with
        `run_startup=False`, so the asyncpg pools created here are reused.

        For standalone `taskiq worker` CLI processes (multi-container layout
        — currently used by `npm run dev:worker`) `app.py` is not imported,
        so this code path doesn't run there at all.
        """
        try:
            from tasks import broker, schedule_source

            if getattr(broker, "_is_started", False):
                return
            await broker.startup()
            app.state.taskiq_broker = broker
            logger.info("TaskIQ broker started (API process)")

            # schedule_source owns its own asyncpg pool (used by `add_schedule`
            # for RECURRING / ONE_TIME_SCHEDULED jobs created through
            # /scheduler/create-job). The scheduler CLI process calls full
            # `startup()` on boot, which truncates `taskiq_schedules` and
            # repopulates it from broker labels — that must NOT run from the
            # API process (would race with the scheduler and clobber dynamic
            # user-added schedules). Initialize only the pool here.
            if getattr(schedule_source, "_database_pool", None) is None:
                import asyncpg

                schedule_source._database_pool = await asyncpg.create_pool(
                    dsn=schedule_source.dsn,
                    **schedule_source._connect_kwargs,
                )
                app.state.taskiq_schedule_source = schedule_source
                logger.info("TaskIQ schedule source pool started (API process)")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to start TaskIQ broker: %s", exc)

    async def _refresh_api_keys(self) -> None:
        """Refresh API keys cache."""
        try:
            from services.api_keys.services import refresh_api_keys_caches

            await refresh_api_keys_caches()
            logger.info("API keys cache refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh API keys cache: {e}")

    async def _initialize_database_connections(self) -> None:
        """Initialize database connection pools and register vector stores."""
        if self.db_type == "PGVECTOR":
            await self._initialize_pgvector()

        # Register the default vector store in the registry
        try:
            from stores.registry import (
                _initialize_default_store,
                get_vector_store_registry,
            )

            registry = get_vector_store_registry()
            _initialize_default_store(registry)
            logger.info("Vector store registry initialized: %s", registry.list_stores())
        except Exception as e:
            logger.error(f"Failed to initialize vector store registry: {e}")

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

    @staticmethod
    async def _initialize_storage(app: Litestar) -> None:
        """Initialize unified file storage backends and service."""
        try:
            from storage import FileLimits, StorageConfig, StorageService, setup_storage
            from storage.lifecycle import register_storage_listeners

            cfg = StorageConfig()
            resolver = await setup_storage(cfg=cfg)

            file_limits = FileLimits(resolver=resolver, cfg=cfg)
            storage_service = StorageService()

            app.state.storage_service = storage_service
            app.state.file_limits = file_limits

            register_storage_listeners(storage_service)

            logger.info("Storage module initialized")
        except Exception as e:
            logger.error("Failed to initialize storage module: %s", e)

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

    async def _maybe_bootstrap_superuser(self) -> None:
        """Create/promote a dev superuser if AUTO_CREATE_SUPERUSER is on.

        Refuses to run in production. Silently no-ops if credentials are
        missing rather than crashing startup, so an empty .env doesn't keep
        the API process from booting.
        """
        if (self.env.get("AUTO_CREATE_SUPERUSER") or "").lower() not in (
            "1",
            "true",
            "t",
            "yes",
            "y",
            "on",
        ):
            return

        env_name = (self.env.get("ENV") or "").strip().lower()
        if env_name == "production":
            logger.warning(
                "AUTO_CREATE_SUPERUSER is enabled but ENV=production — "
                "refusing. Use scripts/bootstrap_superuser.py with "
                "BOOTSTRAP_ALLOW_PRODUCTION=true if this was intentional."
            )
            return

        email = (self.env.get("BOOTSTRAP_SUPERUSER_EMAIL") or "").strip()
        password = self.env.get("BOOTSTRAP_SUPERUSER_PASSWORD") or ""
        if not email or not password:
            logger.warning(
                "AUTO_CREATE_SUPERUSER=true but BOOTSTRAP_SUPERUSER_EMAIL/"
                "PASSWORD are not set — skipping bootstrap."
            )
            return
        if len(password) < 12:
            logger.warning(
                "AUTO_CREATE_SUPERUSER skipped: BOOTSTRAP_SUPERUSER_PASSWORD "
                "is shorter than 12 characters."
            )
            return

        name = (self.env.get("BOOTSTRAP_SUPERUSER_NAME") or "").strip() or None

        try:
            from core.config.app import alchemy
            from services.users.bootstrap import bootstrap_superuser

            async with alchemy.get_session() as session:
                result = await bootstrap_superuser(
                    session,
                    email=email,
                    password=password,
                    name=name,
                    # Don't silently overwrite passwords on every restart.
                    # Operators who need to rotate must run the CLI explicitly.
                    reset_password=False,
                )
                await session.commit()

            if result.created:
                logger.info("Bootstrap superuser created: %s", result.email)
            elif result.updated:
                logger.info("Bootstrap superuser promoted: %s", result.email)
            else:
                logger.info("Bootstrap superuser already present: %s", result.email)
        except Exception as exc:
            # Never block startup on a bootstrap failure — log and move on.
            logger.exception("Bootstrap superuser failed: %s", exc)
