"""
Thin wrappers around the OTel counters for LLM reliability signals.

Keeping the attribute-building logic here (instead of inline at call sites)
means the label shape is consistent across providers, callbacks and the
HTTP layer, and that dashboards / alerts keep working if we ever rename
a label.
"""

from __future__ import annotations

from typing import Any

from services.ai_services.exceptions import (
    LLMEmptyResponseError,
    LLMError,
    LLMGuardrailBlockedError,
    LLMRateLimitError,
    LLMTruncatedError,
)
from services.observability.otel.config import (
    llm_empty_response_counter,
    llm_errors_counter,
    llm_rate_limit_counter,
    llm_router_retries_counter,
)


def _clean(attrs: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in attrs.items() if v is not None}


def record_llm_error(
    *,
    error_type: str,
    source: str,
    provider: str | None = None,
    model: str | None = None,
    status_code: int | None = None,
) -> None:
    llm_errors_counter.add(
        1,
        _clean(
            {
                "error_type": error_type,
                "source": source,
                "provider": provider,
                "model": model,
                "status_code": status_code,
            }
        ),
    )


def record_rate_limit(
    *,
    source: str,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    llm_rate_limit_counter.add(
        1,
        _clean({"source": source, "provider": provider, "model": model}),
    )


def record_empty_response(
    *,
    reason: str,
    finish_reason: str | None = None,
    source: str = "unknown",
    provider: str | None = None,
    model: str | None = None,
) -> None:
    llm_empty_response_counter.add(
        1,
        _clean(
            {
                "reason": reason,
                "finish_reason": finish_reason,
                "source": source,
                "provider": provider,
                "model": model,
            }
        ),
    )


def record_router_retries(
    *,
    retries: int,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    if retries <= 0:
        return
    llm_router_retries_counter.add(
        retries,
        _clean({"provider": provider, "model": model}),
    )


def record_from_exception(exc: LLMError) -> None:
    """Emit error + specialized counters (rate-limit / empty) for a domain LLM error."""
    record_llm_error(
        error_type=type(exc).__name__,
        source=exc.source,
        provider=exc.provider,
        model=exc.model,
        status_code=exc.status_code,
    )
    if isinstance(exc, LLMRateLimitError):
        record_rate_limit(source=exc.source, provider=exc.provider, model=exc.model)
    if isinstance(
        exc, (LLMEmptyResponseError, LLMTruncatedError, LLMGuardrailBlockedError)
    ):
        reason = getattr(exc, "reason", None) or type(exc).__name__
        finish_reason = getattr(exc, "finish_reason", None)
        record_empty_response(
            reason=str(reason),
            finish_reason=finish_reason,
            source=exc.source,
            provider=exc.provider,
            model=exc.model,
        )
