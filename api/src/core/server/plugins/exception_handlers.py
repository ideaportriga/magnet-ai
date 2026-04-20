"""Exception handlers plugin."""

import traceback
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Request, Response
from litestar.exceptions import HTTPException, ValidationException
from litestar.plugins import InitPluginProtocol
from litestar.status_codes import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)

from advanced_alchemy.exceptions import (
    NotFoundError as AlchemyNotFoundError,
)

from core.exceptions import (
    ApplicationError,
    AuthError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError as AppValidationError,
)
from stores import RecordNotFoundError

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


def _is_debug_mode() -> bool:
    from core.config.base import get_settings

    env = get_settings().general.ENV.lower()
    return env in ("", "development", "dev", "local")


def _request_context(request: Request) -> dict:
    """Extract context from request for structured logging."""
    state = getattr(request, "state", {})
    # state may be a Litestar State object or a plain dict
    request_id = (
        state.get("request_id", "")
        if isinstance(state, dict)
        else getattr(state, "request_id", "")
    )
    return {
        "request_id": request_id,
        "path": str(request.url.path),
        "method": request.method,
        "user_id": request.scope.get("user_id", None),
    }


class ExceptionHandlersPlugin(InitPluginProtocol):
    """Plugin to configure exception handlers."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure exception handlers."""
        exception_handlers = dict(app_config.exception_handlers or {})

        exception_handlers.update(
            {
                HTTPException: self._http_error_handler,
                # Application exception hierarchy
                NotFoundError: self._not_found_handler,
                AppValidationError: self._app_validation_handler,
                ConflictError: self._conflict_handler,
                AuthError: self._auth_error_handler,
                ExternalServiceError: self._external_service_handler,
                ApplicationError: self._application_error_handler,
                # Legacy / framework
                RecordNotFoundError: self._not_found_handler,
                # advanced_alchemy raises its own NotFoundError from
                # repository `.get()` when the row is missing. Without
                # this mapping it falls through to the generic
                # Exception handler and returns 500 instead of 404 —
                # the symptom reported on GET /evaluation_sets/:id for
                # missing ids.
                AlchemyNotFoundError: self._not_found_handler,
                LookupError: self._lookup_error_handler,
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

    # -- Application exception hierarchy handlers ----------------------------

    def _not_found_handler(self, _: Request, exc: Exception) -> Response:
        logger.info("Not found: %s", exc)
        return Response(
            content={"error": str(exc) or "The requested resource was not found"},
            status_code=HTTP_404_NOT_FOUND,
        )

    def _app_validation_handler(self, _: Request, exc: AppValidationError) -> Response:
        logger.warning("Validation error: %s", exc)
        return Response(
            content={"error": str(exc)},
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def _conflict_handler(self, _: Request, exc: ConflictError) -> Response:
        logger.warning("Conflict: %s", exc)
        return Response(content={"error": str(exc)}, status_code=409)

    def _auth_error_handler(self, _: Request, exc: AuthError) -> Response:
        logger.warning("Auth error: %s", exc)
        return Response(content={"error": str(exc)}, status_code=401)

    def _external_service_handler(
        self, request: Request, exc: ExternalServiceError
    ) -> Response:
        ctx = _request_context(request)
        logger.error("External service error: %s", exc, exc_info=True, extra=ctx)
        message = str(exc) if _is_debug_mode() else "An external service is unavailable"
        body: dict = {"error": message}
        if ctx.get("request_id"):
            body["request_id"] = ctx["request_id"]
        return Response(content=body, status_code=502)

    def _application_error_handler(self, _: Request, exc: ApplicationError) -> Response:
        """Catch-all for ApplicationError subtypes not handled above."""
        logger.warning("Application error: %s", exc)
        return Response(content={"error": str(exc)}, status_code=400)

    # -- Legacy / framework handlers -----------------------------------------

    def _lookup_error_handler(self, _: Request, exc: LookupError) -> Response:
        """Handle missing configuration references (models, prompts, etc.)."""
        logger.warning("Configuration reference not found: %s", exc)
        return Response(
            content={"error": str(exc)},
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def _unexpected_exception_handler(
        self, request: Request, exc: Exception
    ) -> Response:
        """Handle unexpected exceptions."""
        ctx = _request_context(request)
        tb = traceback.format_exc()
        logger.error("Unhandled %s: %s\n%s", type(exc).__name__, exc, tb, extra=ctx)
        if _is_debug_mode():
            message = str(exc) or f"{type(exc).__name__} (no message)"
        else:
            message = "Internal Server Error"
        body: dict = {"error": message}
        if ctx.get("request_id"):
            body["request_id"] = ctx["request_id"]
        return Response(content=body, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    def _validation_exception_handler(
        self, _: Request, exc: ValidationException
    ) -> Response:
        """Handle validation exceptions."""
        logger.error("Exception: %s", exc, exc_info=True)
        return Response(
            content={"error": "Validation Error", "details": exc.extra},
            status_code=exc.status_code,
        )

    def _sqlalchemy_error_handler(
        self, request: Request, exc: SQLAlchemyError
    ) -> Response:
        """Handle SQLAlchemy database errors with detailed logging."""
        ctx = _request_context(request)
        logger.error("SQLAlchemy error occurred: %s", exc, exc_info=True, extra=ctx)

        # Handle specific SQLAlchemy error types for logging
        if isinstance(exc, IntegrityError):
            logger.error("Integrity constraint violation: %s", exc.orig, extra=ctx)
            status_code = 400
        elif isinstance(exc, OperationalError):
            logger.error("Operational database error: %s", exc.orig, extra=ctx)
            status_code = 500
        elif isinstance(exc, DatabaseError):
            logger.error("Database error: %s", exc.orig, extra=ctx)
            status_code = 500
        else:
            logger.error("General SQLAlchemy error: %s", exc, extra=ctx)
            status_code = 500

        if _is_debug_mode():
            error_details = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
            if isinstance(exc, IntegrityError):
                error_details["constraint_violation"] = (
                    str(exc.orig) if exc.orig else "Unknown constraint violation"
                )
            return Response(
                content={"error": "Database Error", "details": error_details},
                status_code=status_code,
            )

        body: dict = {"error": "Database Error"}
        if ctx.get("request_id"):
            body["request_id"] = ctx["request_id"]
        if isinstance(exc, IntegrityError):
            body["error"] = "A conflicting record already exists"
        return Response(content=body, status_code=status_code)
