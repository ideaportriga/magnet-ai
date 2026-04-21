"""
Validate litellm chat-completion responses before handing them to callers.

The providers can return HTTP 2xx with an unusable body — most commonly when
a guardrail fires (finish_reason=="content_filter") or the response is
truncated with no content produced (finish_reason=="length" and content is
None). Without explicit validation those responses reach HTTP handlers as a
normal 200 with null content, which is indistinguishable from a real success.

This module raises typed domain exceptions so downstream code can convert
them to the right HTTP status (see exceptions.py / plugins/exception_handlers.py)
and so traces turn ERROR on such cases.
"""

from __future__ import annotations

from typing import Any

from services.ai_services.exceptions import (
    ErrorSource,
    LLMEmptyResponseError,
    LLMGuardrailBlockedError,
    LLMTruncatedError,
)


def extract_finish_reason(response: Any) -> str | None:
    """Read finish_reason from the first choice, safely."""
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    first = choices[0]
    return getattr(first, "finish_reason", None)


def extract_request_id(response: Any) -> str | None:
    """Pull x-request-id / x-litellm-call-id / id from the response."""
    rid: str | None = None
    hidden = getattr(response, "_hidden_params", None) or {}
    if isinstance(hidden, dict):
        headers = hidden.get("additional_headers") or {}
        if isinstance(headers, dict):
            rid = headers.get("x-request-id") or headers.get("x-litellm-call-id")
    if not rid:
        rid = getattr(response, "id", None)
    return rid


def extract_deployment_id(response: Any) -> str | None:
    hidden = getattr(response, "_hidden_params", None) or {}
    if isinstance(hidden, dict):
        return hidden.get("model_id")
    return None


def extract_retry_count(response: Any) -> int | None:
    """LiteLLM Router records retry count in _hidden_params when it had to retry."""
    hidden = getattr(response, "_hidden_params", None) or {}
    if not isinstance(hidden, dict):
        return None
    # litellm uses a few different keys across versions
    for key in ("num_retries", "response_ms_retries", "router_retry_count"):
        val = hidden.get(key)
        if isinstance(val, int):
            return val
    return None


def is_cache_hit(response: Any) -> bool:
    hidden = getattr(response, "_hidden_params", None) or {}
    if isinstance(hidden, dict):
        return bool(hidden.get("cache_hit", False))
    return False


def _first_message(response: Any) -> Any | None:
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    return getattr(choices[0], "message", None)


def validate_completion(
    response: Any,
    *,
    model: str | None = None,
    provider: str | None = None,
    source: ErrorSource = "unknown",
) -> None:
    """Validate a chat-completion response.

    Raises one of the domain exceptions from exceptions.py if the response
    is structurally fine (2xx) but carries no usable output.

    Does NOT raise for:
    - finish_reason=="length" when content IS produced (partial answers are usable)
    - finish_reason=="tool_calls" (tool-call responses have no content by design)
    - finish_reason=="stop" with empty-string content (explicit "". e.g. models
      answering "no reply") — models are allowed to choose silence.
    """
    hidden = getattr(response, "_hidden_params", None) or {}
    request_id = extract_request_id(response)

    def _ctx() -> dict[str, Any]:
        return {
            "source": source,
            "provider": provider,
            "model": model,
            "request_id": request_id,
            "hidden_params": hidden if isinstance(hidden, dict) else {},
        }

    choices = getattr(response, "choices", None)
    if not choices:
        raise LLMEmptyResponseError(
            "LLM response contains no choices",
            reason="no_choices",
            **_ctx(),
        )

    finish_reason = extract_finish_reason(response)
    message = _first_message(response)
    content = getattr(message, "content", None) if message is not None else None
    tool_calls = getattr(message, "tool_calls", None) if message is not None else None

    # Guardrail / content filter — always an error
    if finish_reason == "content_filter":
        raise LLMGuardrailBlockedError(
            "LLM response blocked by content filter",
            finish_reason=finish_reason,
            **_ctx(),
        )

    # Truncation with zero content produced — not usable
    if finish_reason == "length" and not content and not tool_calls:
        raise LLMTruncatedError(
            "LLM response truncated before any content was produced",
            finish_reason=finish_reason,
            **_ctx(),
        )

    # tool_calls path — content may legitimately be None
    if tool_calls:
        return

    # Null content without a tool call — broken response
    if content is None:
        raise LLMEmptyResponseError(
            "LLM returned null content with no tool calls",
            reason="null_content",
            finish_reason=finish_reason,
            **_ctx(),
        )


def validate_streamed_completion(
    *,
    aggregated_content: str,
    finish_reason: str | None,
    tool_calls_seen: bool,
    model: str | None = None,
    provider: str | None = None,
    source: ErrorSource = "unknown",
    request_id: str | None = None,
) -> None:
    """Validate a streamed completion after all chunks are consumed.

    The caller is responsible for accumulating content across delta chunks
    and tracking whether any tool_call chunk arrived; this function only
    decides whether the final aggregation is usable.
    """

    def _ctx() -> dict[str, Any]:
        return {
            "source": source,
            "provider": provider,
            "model": model,
            "request_id": request_id,
        }

    if finish_reason == "content_filter":
        raise LLMGuardrailBlockedError(
            "Streamed LLM response blocked by content filter",
            finish_reason=finish_reason,
            **_ctx(),
        )

    if finish_reason == "length" and not aggregated_content and not tool_calls_seen:
        raise LLMTruncatedError(
            "Streamed LLM response truncated before any content was produced",
            finish_reason=finish_reason,
            **_ctx(),
        )

    if tool_calls_seen:
        return

    if not aggregated_content and finish_reason not in (None, "stop"):
        # Finished for a non-normal reason and produced nothing
        raise LLMEmptyResponseError(
            "Streamed LLM response produced no content",
            reason="empty_stream",
            finish_reason=finish_reason,
            **_ctx(),
        )
