"""Simplified application factory using plugins."""

import asyncio
import os
from logging import getLogger

# Load + validate environment BEFORE anything imports get_general_settings(),
# otherwise get_env() snapshots an empty SECRET_ENCRYPTION_KEY into the
# lru_cache and later Fernet decryption of providers.secrets_encrypted
# fails with InvalidToken. See BACKEND_FIXES_ROADMAP.md §A.3.
from config.config import load_env as _load_env

_load_env()

from litestar import Litestar  # noqa: E402

from core.server.plugin_registry import (  # noqa: E402
    alchemy,
    cors_plugin,
    dependencies_plugin,
    exception_handlers_plugin,
    middleware_plugin,
    openapi_plugin,
    oracle_monitoring_plugin,
    problem_details,
    shutdown_plugin,
    startup_plugin,
    structlog,
)
from routes import get_route_handlers  # noqa: E402
from core.config.base import (  # noqa: E402
    get_auth_settings,
    get_vector_database_settings,
    get_general_settings,
    get_log_settings,
)

env = os.environ

WEB_INCLUDED = env.get("WEB_INCLUDED") == "true"

logger = getLogger(__name__)

auth_settings = get_auth_settings()
db_connection_settings = get_vector_database_settings()
general_settings = get_general_settings()
log_settings = get_log_settings()

AUTH_ENABLED = auth_settings.AUTH_ENABLED
VECTOR_DB_TYPE = db_connection_settings.VECTOR_DB_TYPE
DEBUG_MODE = log_settings.DEBUG_MODE


def create_app() -> Litestar:
    """Create the Litestar application with plugins."""
    route_handlers = get_route_handlers(
        auth_enabled=AUTH_ENABLED, web_included=WEB_INCLUDED
    )

    # Create the application with all plugins
    max_upload_mb = int(os.environ.get("MAX_UPLOAD_FILE_SIZE_MB", "50"))

    app = Litestar(
        route_handlers=route_handlers,
        debug=DEBUG_MODE,
        request_max_body_size=max_upload_mb * 1024 * 1024,
        plugins=[
            # Core plugins
            alchemy,
            problem_details,
            structlog,
            # Custom plugins
            cors_plugin,
            dependencies_plugin,
            exception_handlers_plugin,
            middleware_plugin,
            openapi_plugin,
            shutdown_plugin,
            startup_plugin,
        ],
    )

    # Add Oracle monitoring if needed
    if VECTOR_DB_TYPE == "ORACLE":
        app.after_request = oracle_monitoring_plugin.after_request

    return app


# Create the app instance
app = create_app()

# Enable asyncio debug mode once the loop exists so slow_callback_duration and
# set_debug aren't applied to a loop that will be replaced by the ASGI runner.
if DEBUG_MODE:
    try:
        loop = asyncio.get_event_loop()
        loop.slow_callback_duration = 0.1  # 100ms — surface blocking calls
        loop.set_debug(True)
        logger.info("asyncio debug enabled (slow_callback_duration=100ms)")
    except RuntimeError:
        # No current loop (e.g. import-time in some deploy targets) — ASGI
        # runner will create its own; debug settings will be applied via env.
        logger.debug("No running event loop at import time; asyncio debug skipped")
