"""
Helpers for calling litellm and translating its exceptions to domain errors.

Usage:

    async with litellm_call_context(source="router", model=model, provider=prov):
        response = await router.acompletion(**params)

On a litellm.exceptions.* the raw exception is caught, converted to the
matching `LLMError` subclass and re-raised. Callers can then catch `LLMError`
uniformly and downstream HTTP / trace layers can inspect `error.source`,
`error.status_code`, `error.provider`, etc.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import litellm

from services.ai_services.exceptions import (
    ErrorSource,
    LLMContextWindowExceededError,
    LLMError,
    LLMGuardrailBlockedError,
    LLMProviderAPIError,
    LLMProviderAuthError,
    LLMProviderBadRequestError,
    LLMProviderServiceUnavailableError,
    LLMRateLimitError,
    LLMTimeoutError,
)


def _llm_provider(exc: Any) -> str | None:
    return getattr(exc, "llm_provider", None)


def _status_code(exc: Any) -> int | None:
    val = getattr(exc, "status_code", None)
    if isinstance(val, int):
        return val
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _retry_after(exc: Any) -> float | None:
    resp = getattr(exc, "response", None)
    if resp is not None:
        headers = getattr(resp, "headers", None)
        if headers:
            try:
                ra = headers.get("retry-after") or headers.get("Retry-After")
                if ra is not None:
                    return float(ra)
            except (TypeError, ValueError):
                return None
    return None


def translate_litellm_exception(
    exc: BaseException,
    *,
    source: ErrorSource,
    model: str | None,
    provider: str | None,
) -> Exception:
    """Map a raw litellm exception to a domain `LLMError` subclass.

    If the exception is not from litellm, the original exception is returned
    unchanged (callers should `raise` it).
    """
    message = str(exc)
    ctx: dict[str, Any] = {
        "source": source,
        "provider": provider or _llm_provider(exc),
        "model": model or getattr(exc, "model", None),
        "status_code": _status_code(exc),
    }

    if isinstance(exc, litellm.exceptions.RateLimitError):
        return LLMRateLimitError(message, retry_after=_retry_after(exc), **ctx)

    if isinstance(exc, litellm.exceptions.Timeout):
        return LLMTimeoutError(message, **ctx)

    if isinstance(exc, litellm.exceptions.ContextWindowExceededError):
        return LLMContextWindowExceededError(message, **ctx)

    if isinstance(exc, litellm.exceptions.ContentPolicyViolationError):
        return LLMGuardrailBlockedError(
            message, finish_reason="content_policy_violation", **ctx
        )

    if isinstance(exc, litellm.exceptions.AuthenticationError):
        return LLMProviderAuthError(message, **ctx)

    if isinstance(
        exc,
        (
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.InternalServerError,
            litellm.exceptions.BadGatewayError,
        ),
    ):
        return LLMProviderServiceUnavailableError(message, **ctx)

    if isinstance(
        exc,
        (
            litellm.exceptions.BadRequestError,
            litellm.exceptions.UnprocessableEntityError,
            litellm.exceptions.UnsupportedParamsError,
        ),
    ):
        return LLMProviderBadRequestError(message, **ctx)

    if isinstance(exc, litellm.exceptions.APIError):
        return LLMProviderAPIError(message, **ctx)

    # Not a litellm exception — let it through untouched
    return exc  # type: ignore[return-value]


@asynccontextmanager
async def litellm_call_context(
    *,
    source: ErrorSource,
    model: str | None = None,
    provider: str | None = None,
):
    """Catch litellm.exceptions.* and re-raise as domain LLMError.

    All litellm exceptions derive from `litellm.exceptions.APIError`
    (which itself extends `OpenAIError`), so a single `except` clause
    covers the whole family including `Timeout`.
    """
    try:
        yield
    except litellm.exceptions.APIError as e:
        translated = translate_litellm_exception(
            e, source=source, model=model, provider=provider
        )
        if translated is e:
            raise
        # Record before re-raising so metric-on-failure is not lost
        # if the caller swallows the exception.
        from services.ai_services.metrics import record_from_exception

        if isinstance(translated, LLMError):
            record_from_exception(translated)
        raise translated from e
