"""
LiteLLM callback bridge for Magnet AI observability.

The callback is registered once at startup (see `core/server/plugins/startup.py`)
and receives success / failure events from every LiteLLM call — completion,
embedding, rerank, transcription, speech — regardless of which code path
initiated it.

For each event it:

1. Writes a line to the Python logger (picked up by the Loki handler).
2. Enriches the *currently active* OpenTelemetry span with
   `gen_ai.response.*` / `llm.*` attributes, so the same span that the
   caller opened via `observability_context.observe_feature(...)` is
   the one that carries cache-hit / deployment-id / request-id / etc.
3. On failure, marks that span as ERROR and calls `record_exception`
   so traces turn red on real errors (including provider rate limits,
   guardrails, timeouts).

The callback runs inside the caller's async context, so
`trace.get_current_span()` returns the caller's span — no need to pass
a span handle through LiteLLM.
"""

from __future__ import annotations

import logging
from typing import Any

from litellm.integrations.custom_logger import CustomLogger
from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

from services.ai_services.exceptions import LLMError
from services.ai_services.metrics import record_llm_error
from services.ai_services.response_validation import (
    extract_deployment_id,
    extract_request_id,
    extract_retry_count,
    is_cache_hit,
)

logger = logging.getLogger(__name__)


def _active_span() -> Span | None:
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx is None or not ctx.is_valid:
        return None
    return span


def _safe_set_attribute(span: Span, key: str, value: Any) -> None:
    if value is None:
        return
    try:
        span.set_attribute(key, value)
    except Exception:  # pragma: no cover — attribute setting must never fail a request
        logger.debug("Failed to set span attribute %s", key, exc_info=True)


def _retry_after_from_exception(exc: BaseException | None) -> float | None:
    if exc is None:
        return None
    resp = getattr(exc, "response", None)
    if resp is None:
        return None
    headers = getattr(resp, "headers", None)
    if not headers:
        return None
    try:
        ra = headers.get("retry-after") or headers.get("Retry-After")
        return float(ra) if ra is not None else None
    except (TypeError, ValueError):
        return None


class MagnetAILogger(CustomLogger):
    """LiteLLM callback that enriches the active OTel span with response metadata."""

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        try:
            model = kwargs.get("model", "unknown")
            call_type = kwargs.get("call_type", "completion")
            duration = (
                (end_time - start_time).total_seconds()
                if start_time and end_time
                else 0
            )

            hidden = getattr(response_obj, "_hidden_params", None) or {}
            cost = hidden.get("response_cost", 0.0) if isinstance(hidden, dict) else 0.0

            usage_info: dict[str, int] = {}
            if hasattr(response_obj, "usage") and response_obj.usage:
                usage = response_obj.usage
                usage_info = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                }

            cache_hit = is_cache_hit(response_obj)
            request_id = extract_request_id(response_obj)
            deployment_id = extract_deployment_id(response_obj)
            retry_count = extract_retry_count(response_obj)

            # finish_reason — chat completions only
            finish_reason: str | None = None
            choices = getattr(response_obj, "choices", None)
            if choices:
                finish_reason = getattr(choices[0], "finish_reason", None)

            # Enrich active OTel span so these fields are visible on the trace
            # that the caller opened, not on a separate callback span.
            span = _active_span()
            if span is not None:
                _safe_set_attribute(span, "llm.cache_hit", cache_hit)
                _safe_set_attribute(span, "llm.router.deployment_id", deployment_id)
                _safe_set_attribute(span, "llm.router.retry_count", retry_count)
                _safe_set_attribute(span, "gen_ai.response.id", request_id)
                _safe_set_attribute(span, "gen_ai.request.id", request_id)
                if finish_reason:
                    _safe_set_attribute(
                        span, "gen_ai.response.finish_reason", finish_reason
                    )
                if usage_info:
                    _safe_set_attribute(
                        span, "gen_ai.usage.input_tokens", usage_info["prompt_tokens"]
                    )
                    _safe_set_attribute(
                        span,
                        "gen_ai.usage.output_tokens",
                        usage_info["completion_tokens"],
                    )
                if cost:
                    _safe_set_attribute(span, "gen_ai.usage.cost", cost)

            logger.debug(
                "LiteLLM %s success: model=%s, duration=%.2fs, cost=$%.6f, "
                "tokens=%s, cache_hit=%s, request_id=%s, deployment_id=%s, "
                "retries=%s, finish_reason=%s",
                call_type,
                model,
                duration,
                cost,
                usage_info.get("total_tokens", 0),
                cache_hit,
                request_id,
                deployment_id,
                retry_count,
                finish_reason,
            )

        except Exception:
            logger.debug(
                "Error in MagnetAILogger.async_log_success_event", exc_info=True
            )

    async def async_log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        try:
            model = kwargs.get("model", "unknown")
            call_type = kwargs.get("call_type", "completion")
            exception = kwargs.get("exception")
            duration = (
                (end_time - start_time).total_seconds()
                if start_time and end_time
                else 0
            )

            error_str = str(exception)[:500] if exception else "unknown"
            error_type = type(exception).__name__ if exception else "unknown"
            status_code: int | None = None
            llm_provider: str | None = None
            if exception is not None:
                sc = getattr(exception, "status_code", None)
                if isinstance(sc, int):
                    status_code = sc
                llm_provider = getattr(exception, "llm_provider", None)
            retry_after = _retry_after_from_exception(exception)

            # Mark the caller's span as ERROR so "green success" traces stop
            # appearing on real failures.
            span = _active_span()
            if span is not None:
                if exception is not None:
                    try:
                        span.record_exception(exception)
                    except Exception:  # pragma: no cover
                        logger.debug("Failed to record_exception", exc_info=True)
                span.set_status(StatusCode.ERROR, description=error_type)
                _safe_set_attribute(span, "error.type", error_type)
                _safe_set_attribute(span, "error.message", error_str)
                _safe_set_attribute(span, "llm.error.provider", llm_provider)
                if status_code is not None:
                    _safe_set_attribute(span, "http.status_code", status_code)
                if retry_after is not None:
                    _safe_set_attribute(span, "llm.retry_after", retry_after)

            # Fallback metric: if the translator already recorded the domain
            # exception, skip to avoid double-counting. Otherwise this
            # captures non-litellm failures (e.g. network errors that
            # slipped through).
            if exception is not None and not isinstance(exception, LLMError):
                record_llm_error(
                    error_type=error_type,
                    source="unknown",
                    provider=llm_provider,
                    model=model,
                    status_code=status_code,
                )

            logger.error(
                "LiteLLM %s failure: model=%s, duration=%.2fs, error_type=%s, "
                "status_code=%s, provider=%s, retry_after=%s, error=%s",
                call_type,
                model,
                duration,
                error_type,
                status_code,
                llm_provider,
                retry_after,
                error_str,
            )

        except Exception:
            logger.debug(
                "Error in MagnetAILogger.async_log_failure_event", exc_info=True
            )

    async def async_log_stream_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        # Streaming events share the structure of success events
        await self.async_log_success_event(kwargs, response_obj, start_time, end_time)
