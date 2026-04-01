"""Application-wide exception hierarchy.

All domain-specific exceptions should inherit from ``ApplicationError`` so that
the global exception handlers can distinguish *expected* business errors from
truly *unexpected* failures.

Mapping to HTTP status codes is handled by
``core.server.plugins.exception_handlers``.
"""


class ApplicationError(Exception):
    """Base for all expected application errors."""


# --- Client errors (4xx) ---------------------------------------------------


class ValidationError(ApplicationError):
    """Invalid input data that cannot be processed."""


class NotFoundError(ApplicationError):
    """Requested resource does not exist."""


class ConflictError(ApplicationError):
    """Operation conflicts with current state (duplicate, race condition)."""


class AuthError(ApplicationError):
    """Authentication or authorisation failure."""


# --- External / infrastructure errors (5xx) ---------------------------------


class ExternalServiceError(ApplicationError):
    """An external dependency failed."""


class StorageError(ExternalServiceError):
    """File / blob storage operation failed (Azure Blob, S3, …)."""


class VectorDBError(ExternalServiceError):
    """Vector database operation failed (Qdrant, PGVector, …)."""


class LLMProviderError(ExternalServiceError):
    """LLM provider returned an unrecoverable error after retries."""


# --- Domain-specific groupings ----------------------------------------------


class SchedulerError(ApplicationError):
    """Scheduler / job management error."""


class KnowledgeGraphError(ApplicationError):
    """Knowledge-graph pipeline error."""
