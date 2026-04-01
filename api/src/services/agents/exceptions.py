"""Custom exceptions for the agent system.

Provides specific exception types for different failure scenarios
so callers can handle them appropriately.
"""

from core.exceptions import ApplicationError


class AgentError(ApplicationError):
    """Base exception for all agent-related errors."""


class AgentNotFoundError(AgentError):
    """Raised when an agent cannot be found by system_name or config."""


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid or incomplete (e.g. missing topic, provider, tool)."""


class ClassificationError(AgentError):
    """Raised when conversation classification fails."""


class ActionExecutionError(AgentError):
    """Raised when an agent action fails to execute."""


class AgentLoopExhaustedError(AgentError):
    """Raised when the agent loop reaches the maximum number of iterations without producing a response."""


class AgentTimeoutError(AgentError):
    """Raised when the agent topic execution exceeds the configured timeout."""
