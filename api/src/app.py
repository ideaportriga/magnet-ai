import asyncio
import atexit
import os
from logging import getLogger

from litestar import Litestar, Request, Response
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.exceptions import HTTPException, ValidationException
from litestar.openapi import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.types import Middleware
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.tags import get_tags
from core.server.plugins import alchemy, problem_details, structlog
from middlewares.auth import create_auth_middleware
from middlewares.database_error import DatabaseErrorLoggingMiddleware
from routes import get_route_handlers
from scheduler import create_scheduler, get_scheduler
from services.api_keys.services import refresh_api_keys_caches
from stores import get_db_client
from stores.oracle.client import OracleDbClient

logger = getLogger(__name__)

env = os.environ
AUTH_ENABLED = env.get("AUTH_ENABLED") == "true"
AUTH_ENABLED_FOR_SCHEMA = env.get("AUTH_ENABLED_FOR_SCHEMA") == "true"
WEB_INCLUDED = env.get("WEB_INCLUDED") == "true"
DB_TYPE = env.get("DB_TYPE")
EVENT_LOOP_DEBUG = env.get("EVENT_LOOP_DEBUG") == "true"


async def on_startup(app: Litestar) -> None:
    """Startup event handler"""
    logger.info("Starting application...")

    try:
        scheduler = await create_scheduler()
        app.state.scheduler = scheduler
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        # Set scheduler to None so we can handle it in shutdown
        app.state.scheduler = None
        # Don't raise the exception to allow the app to start without scheduler
        # raise e  # Uncomment if you want the app to fail to start without scheduler

    if AUTH_ENABLED:
        await refresh_api_keys_caches()

    # Initialize database connection pools based on DB_TYPE
    if DB_TYPE == "PGVECTOR":
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

    # SQLAlchemy is automatically initialized by the plugin
    logger.info("SQLAlchemy engine initialized via plugin")

    # Initialize bots runtime cache
    try:
        from services.bots.runtime_cache import BotRuntimeCache

        app.state.bot_runtime_cache = BotRuntimeCache()
        logger.info("BotRuntimeCache successfully initialized")
    except Exception as e:
        logger.error(f"Failed to initialize BotRuntimeCache: {e}")


async def on_shutdown(app: Litestar) -> None:
    """Shutdown event handler"""
    logger.info("Shutting down application...")

    # First, shut down the scheduler to prevent new jobs from starting
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        try:
            logger.info("Shutting down scheduler...")
            # Try with wait parameter first, fallback to basic shutdown if not supported
            try:
                scheduler.shutdown(wait=True)  # Wait for current jobs to complete
            except TypeError:
                # Fallback for schedulers that don't support wait parameter
                scheduler.shutdown()
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    else:
        logger.info("No scheduler to shut down")

    # Give a brief moment for any ongoing operations to complete
    await asyncio.sleep(0.5)

    # SQLAlchemy engine will be closed automatically by the plugin

    # Close database connection pools based on DB_TYPE
    if DB_TYPE == "ORACLE":
        logger.info("Closing Oracle connection pool...")

        async def close_connection_pool():
            client = get_db_client()
            await client.close_pool()

        atexit.register(close_connection_pool)
    elif DB_TYPE == "PGVECTOR":
        logger.info("Closing PgVector connection pool...")
        try:
            from stores.pgvector_db import pgvector_client

            await pgvector_client.close_pool()
            logger.info("PgVector connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing PgVector connection pool: {e}")


cors_config = None
CORS_OVERRIDE_ALLOWED_ORIGINS = env.get("CORS_OVERRIDE_ALLOWED_ORIGINS", "").split(",")

if CORS_OVERRIDE_ALLOWED_ORIGINS:
    cors_config = CORSConfig(
        allow_origins=CORS_OVERRIDE_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

middlewares: list[Middleware] = [
    DatabaseErrorLoggingMiddleware,
]

if AUTH_ENABLED:
    exclude_param = []
    
    if AUTH_ENABLED_FOR_SCHEMA:
        exclude_param.append("schema")

    middlewares.append(create_auth_middleware(exclude_param=exclude_param))


def http_error_handler(_: Request, exc: HTTPException) -> Response:
    logger.info("HTTP error: %s", exc)
    return Response(content={"error": exc.detail}, status_code=exc.status_code)


def unexpected_exception_handler(_: Request, exc: Exception) -> Response:
    logger.error("Exception: %s", exc, exc_info=True)
    return Response(
        content={"error": str(exc)},
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


def validation_exception_handler(_: Request, exc: ValidationException) -> Response:
    """Handles validation exceptions"""
    logger.error("Exception: %s", exc, exc_info=True)
    return Response(
        content={"error": "Validation Error", "details": exc.extra},
        status_code=exc.status_code,
    )


def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError) -> Response:
    """Handles SQLAlchemy database errors with detailed logging"""
    logger.error("SQLAlchemy error occurred: %s", exc, exc_info=True)

    # Log the specific error details
    error_details = {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }

    # Handle specific SQLAlchemy error types
    if isinstance(exc, IntegrityError):
        logger.error("Integrity constraint violation: %s", exc.orig)
        error_details["constraint_violation"] = (
            str(exc.orig) if exc.orig else "Unknown constraint violation"
        )
        status_code = 400
    elif isinstance(exc, OperationalError):
        logger.error("Operational database error: %s", exc.orig)
        error_details["operational_error"] = (
            str(exc.orig) if exc.orig else "Database operational error"
        )
        status_code = 500
    elif isinstance(exc, DatabaseError):
        logger.error("Database error: %s", exc.orig)
        error_details["database_error"] = (
            str(exc.orig) if exc.orig else "Database error"
        )
        status_code = 500
    else:
        logger.error("General SQLAlchemy error: %s", exc)
        status_code = 500

    return Response(
        content={"error": "Database Error", "details": error_details},
        status_code=status_code,
    )


openapi_config = OpenAPIConfig(
    title="Magnet AI API",
    version="0.1",  # TODO - retrieve from env variable
    security=[{"ApiKeyAuth": []}],
    tags=get_tags(),
    components=Components(
        security_schemes={
            "ApiKeyAuth": SecurityScheme(
                type="apiKey",
                security_scheme_in="header",
                name="x-api-key",
            ),
        },
    ),
)

route_handlers = get_route_handlers(auth_enabled=AUTH_ENABLED, web_included=WEB_INCLUDED)


async def get_user_id(request: Request):
    return request.scope.get("user_id")


async def get_db_session(request: Request) -> AsyncSession:
    """Get database session from request state."""
    return request.state.db_session


app = Litestar(
    route_handlers=route_handlers,
    openapi_config=openapi_config,
    cors_config=cors_config,
    middleware=middlewares,
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    debug=False,
    exception_handlers={
        HTTPException: http_error_handler,
        SQLAlchemyError: sqlalchemy_error_handler,
        IntegrityError: sqlalchemy_error_handler,
        OperationalError: sqlalchemy_error_handler,
        DatabaseError: sqlalchemy_error_handler,
        ValidationException: validation_exception_handler,
        Exception: unexpected_exception_handler,
    },
    dependencies={
        "scheduler": Provide(get_scheduler, sync_to_thread=False),
        "user_id": Provide(get_user_id),
    },
    plugins=[alchemy, problem_details, structlog],
)

if DB_TYPE == "ORACLE":

    async def after_request(response: Response) -> Response:
        client = get_db_client()

        if isinstance(client, OracleDbClient):
            logger.info(
                f"Oracle connection pool: opened {client._pool.opened}, busy {client._pool.busy}",
            )

        return response

    app.after_request = after_request


if EVENT_LOOP_DEBUG:
    asyncio.get_event_loop().set_debug(True)
