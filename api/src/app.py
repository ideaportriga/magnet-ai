"""Simplified application factory using plugins."""

import asyncio
import os
from logging import getLogger

from litestar import Litestar

from core.server.plugin_registry import (
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
from routes import get_route_handlers
from core.config.base import get_auth_settings, get_database_connection_settings, get_general_settings
env = os.environ

WEB_INCLUDED = env.get("WEB_INCLUDED") == "true"

logger = getLogger(__name__)

auth_settings = get_auth_settings()
db_connection_settings = get_database_connection_settings()
general_settings = get_general_settings()

AUTH_ENABLED = auth_settings.AUTH_ENABLED
DB_TYPE = db_connection_settings.DB_TYPE
EVENT_LOOP_DEBUG = general_settings.EVENT_LOOP_DEBUG


def create_app() -> Litestar:
    """Create the Litestar application with plugins."""
    route_handlers = get_route_handlers(auth_enabled=AUTH_ENABLED, web_included=WEB_INCLUDED)

    # Create the application with all plugins
    app = Litestar(
        route_handlers=route_handlers,
        debug=False,
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
    if DB_TYPE == "ORACLE":
        app.after_request = oracle_monitoring_plugin.after_request

    return app


# Create the app instance
app = create_app()

# Enable event loop debug if requested
if EVENT_LOOP_DEBUG:
    asyncio.get_event_loop().set_debug(True)
