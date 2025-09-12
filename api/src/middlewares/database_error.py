"""
Middleware for handling and logging database errors
"""

import logging
from typing import TYPE_CHECKING

from litestar.middleware.base import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DatabaseErrorLoggingMiddleware(AbstractMiddleware):
    """Middleware to catch and log database errors with detailed information"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process request and catch any database errors for detailed logging
        """

        async def send_wrapper(message: Message) -> None:
            """Wrap send to catch database errors"""
            try:
                await send(message)
            except SQLAlchemyError as exc:
                # Log detailed information about the database error
                logger.error(
                    "Database error in middleware: %s. Error details: %s",
                    type(exc).__name__,
                    str(exc),
                    exc_info=True,
                )

                # If this is an original exception with details, log them
                if hasattr(exc, "orig") and getattr(exc, "orig", None):
                    logger.error("Original database error: %s", getattr(exc, "orig"))

                # If this has statement information, log it
                if hasattr(exc, "statement") and getattr(exc, "statement", None):
                    logger.error("Failed SQL statement: %s", getattr(exc, "statement"))

                # If this has params, log them (be careful with sensitive data)
                if hasattr(exc, "params") and getattr(exc, "params", None):
                    logger.error("SQL parameters: %s", getattr(exc, "params"))

                # Re-raise the exception so it can be handled by exception handlers
                raise
            except Exception as exc:
                # Log any other unexpected errors
                logger.error(
                    "Unexpected error in database middleware: %s", exc, exc_info=True
                )
                raise

        await self.app(scope, receive, send_wrapper)
