# Add logging configuration for SQLAlchemy
import logging
import sys
from functools import lru_cache

import structlog
from litestar.config.compression import CompressionConfig
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.problem_details import ProblemDetailsConfig
from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.plugins.structlog import StructlogConfig

from .base import get_settings

settings = get_settings()


compression = CompressionConfig(backend="gzip")

alchemy = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler="autocommit",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)

problem_details = ProblemDetailsConfig(enable_for_all_http_exceptions=True)


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


_render_as_json = not _is_tty()

# Console processors (human-readable or JSON based on TTY)
_structlog_default_processors = default_structlog_processors(as_json=_render_as_json)
_structlog_default_processors.insert(1, structlog.processors.EventRenamer("message"))
_structlog_default_processors.insert(
    2,
    structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        ]
    ),
)

# Standard lib processors for console (human-readable or JSON based on TTY)
_structlog_standard_lib_processors = default_structlog_standard_lib_processors(
    as_json=_render_as_json
)
_structlog_standard_lib_processors.insert(
    1, structlog.processors.EventRenamer("message")
)
_structlog_standard_lib_processors.insert(
    2,
    structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        ]
    ),
)

# Loki processors (always JSON for structured logging in Loki)
_structlog_loki_processors = default_structlog_standard_lib_processors(as_json=True)
_structlog_loki_processors.insert(1, structlog.processors.EventRenamer("message"))
_structlog_loki_processors.insert(
    2,
    structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        ]
    ),
)

# Handlers configuration - console + optionally Loki
_default_handlers = ["queue_listener"] + (["loki"] if settings.log.LOKI_URL else [])
_console_only_handlers = [
    "queue_listener"
]  # For urllib3/requests to avoid infinite loop

log = StructlogConfig(
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        processors=_structlog_default_processors,
        logger_factory=default_logger_factory(as_json=_render_as_json),
        standard_lib_logging_config=LoggingConfig(
            root={
                "level": logging.getLevelName(settings.log.LEVEL),
                "handlers": _default_handlers,
            },
            formatters={
                "standard": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": _structlog_standard_lib_processors,
                },
                "loki": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": _structlog_loki_processors,
                },
            },
            handlers={
                "loki": {
                    "class": "logging_loki.LokiHandler",
                    "url": settings.log.LOKI_URL,
                    "tags": {"application": "magnet-ai"},
                    "version": "1",
                    "formatter": "loki",
                }
            }
            if settings.log.LOKI_URL
            else {},
            loggers={
                # Uvicorn ASGI server
                "uvicorn": {
                    "propagate": False,
                    "level": settings.log.ASGI_ERROR_LEVEL,
                    "handlers": _default_handlers,
                },
                "uvicorn.access": {
                    "propagate": False,
                    "level": settings.log.ASGI_ACCESS_LEVEL,
                    "handlers": _default_handlers,
                },
                # Database
                "sqlalchemy.engine": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": _default_handlers,
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": _default_handlers,
                },
                # HTTP clients
                "httpx": {
                    "propagate": False,
                    "level": settings.log.LEVEL,
                    "handlers": _default_handlers,
                },
                # AI/ML
                "openai": {
                    "propagate": False,
                    "level": settings.log.LEVEL,
                    "handlers": _default_handlers,
                },
                # Exclude urllib3 and requests from Loki to prevent infinite loop
                # Set to WARNING to reduce noise from Loki's HTTP client
                "urllib3": {
                    "propagate": False,
                    "level": logging.WARNING,
                    "handlers": _console_only_handlers,
                },
                "requests": {
                    "propagate": False,
                    "level": logging.WARNING,
                    "handlers": _console_only_handlers,
                },
            },
        ),
    ),
    middleware_logging_config=LoggingMiddlewareConfig(
        request_log_fields=settings.log.REQUEST_FIELDS,
        response_log_fields=settings.log.RESPONSE_FIELDS,
    ),
)
