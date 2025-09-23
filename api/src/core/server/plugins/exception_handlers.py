"""Exception handlers plugin."""

from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Request, Response
from litestar.exceptions import HTTPException, ValidationException
from litestar.plugins import InitPluginProtocol
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


class ExceptionHandlersPlugin(InitPluginProtocol):
    """Plugin to configure exception handlers."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure exception handlers."""
        exception_handlers = dict(app_config.exception_handlers or {})

        exception_handlers.update(
            {
                HTTPException: self._http_error_handler,
                SQLAlchemyError: self._sqlalchemy_error_handler,
                IntegrityError: self._sqlalchemy_error_handler,
                OperationalError: self._sqlalchemy_error_handler,
                DatabaseError: self._sqlalchemy_error_handler,
                ValidationException: self._validation_exception_handler,
                Exception: self._unexpected_exception_handler,
            }
        )

        app_config.exception_handlers = exception_handlers
        return app_config

    def _http_error_handler(self, _: Request, exc: HTTPException) -> Response:
        """Handle HTTP exceptions."""
        logger.info("HTTP error: %s", exc)
        return Response(content={"error": exc.detail}, status_code=exc.status_code)

    def _unexpected_exception_handler(self, _: Request, exc: Exception) -> Response:
        """Handle unexpected exceptions."""
        logger.error("Exception: %s", exc, exc_info=True)
        return Response(
            content={"error": str(exc)},
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def _validation_exception_handler(
        self, _: Request, exc: ValidationException
    ) -> Response:
        """Handle validation exceptions."""
        logger.error("Exception: %s", exc, exc_info=True)
        return Response(
            content={"error": "Validation Error", "details": exc.extra},
            status_code=exc.status_code,
        )

    def _sqlalchemy_error_handler(self, _: Request, exc: SQLAlchemyError) -> Response:
        """Handle SQLAlchemy database errors with detailed logging."""
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
