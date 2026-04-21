"""
Domain exceptions for LiteLLM-based AI services.

Wraps raw litellm.exceptions.* into typed application errors that carry:
- The source layer (router / provider / proxy) so rate limits from our
  Router are distinguishable from upstream provider 429s.
- finish_reason and hidden_params so a guardrail block or a truncation
  can be inspected downstream.
- Optional retry_after / status_code / request_id to map cleanly to HTTP.

These exceptions are raised from BaseLiteLLMProvider and caught by the
application-level exception handler (see core/server/plugins/exception_handlers.py).
"""

from __future__ import annotations

from typing import Any, Literal

ErrorSource = Literal["router", "provider", "proxy", "unknown"]


class LLMError(Exception):
    """Base class for all LLM-layer domain errors."""

    http_status_code: int = 502

    def __init__(
        self,
        message: str,
        *,
        source: ErrorSource = "unknown",
        provider: str | None = None,
        model: str | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
        hidden_params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.source = source
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.request_id = request_id
        self.hidden_params = hidden_params or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "source": self.source,
            "provider": self.provider,
            "model": self.model,
            "status_code": self.status_code,
            "request_id": self.request_id,
        }


# --- Response-shape errors (no exception from litellm, but the reply is unusable) ---


class LLMEmptyResponseError(LLMError):
    """Provider returned 2xx but the response carries no usable content.

    Covers:
    - empty choices list
    - choices[0].message.content is None AND no tool_calls
    """

    http_status_code = 502

    def __init__(
        self,
        message: str = "LLM returned empty response",
        *,
        reason: str = "null_content",
        finish_reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.reason = reason
        self.finish_reason = finish_reason


class LLMGuardrailBlockedError(LLMError):
    """Response was blocked by a content filter / guardrail (finish_reason=content_filter)."""

    http_status_code = 422

    def __init__(
        self,
        message: str = "LLM response blocked by content filter",
        *,
        finish_reason: str = "content_filter",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.finish_reason = finish_reason


class LLMTruncatedError(LLMError):
    """Response was cut off by max_tokens and no content was produced.

    Non-empty truncated responses are not raised — they are still usable.
    Only raised when finish_reason=="length" AND content is empty.
    """

    http_status_code = 502

    def __init__(
        self,
        message: str = "LLM response truncated before any content was produced",
        *,
        finish_reason: str = "length",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.finish_reason = finish_reason


# --- Exceptions from litellm, re-raised as domain errors ---


class LLMRateLimitError(LLMError):
    """Rate limit hit at provider, router or proxy level."""

    http_status_code = 429

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    http_status_code = 504


class LLMContextWindowExceededError(LLMError):
    """Input tokens exceeded the model's context window."""

    http_status_code = 400


class LLMProviderAuthError(LLMError):
    """Invalid / expired credentials. Our misconfiguration, not the client's fault."""

    http_status_code = 502


class LLMProviderBadRequestError(LLMError):
    """Provider rejected the request as malformed (400)."""

    http_status_code = 400


class LLMProviderServiceUnavailableError(LLMError):
    """Provider is unavailable (503 / 502 / 504 from upstream)."""

    http_status_code = 502


class LLMProviderAPIError(LLMError):
    """Catch-all for other provider API errors."""

    http_status_code = 502
