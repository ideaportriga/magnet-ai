"""
LiteLLM Callback Logger for Magnet AI observability.

Integrates LiteLLM's callback system with the application's observability layer.
All LiteLLM calls (completion, embedding, rerank, transcription, speech) are
automatically tracked for duration, cost, and usage.

Usage:
    Register at application startup:

        from services.ai_services.callbacks import MagnetAILogger
        import litellm

        litellm.callbacks = [MagnetAILogger()]

    Or append to existing callbacks:

        litellm.callbacks.append(MagnetAILogger())
"""

import logging
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

logger = logging.getLogger(__name__)


class MagnetAILogger(CustomLogger):
    """
    LiteLLM callback that integrates with Magnet AI observability.

    Automatically captures:
    - All LiteLLM API calls (completion, embedding, rerank, transcription, speech)
    - Response cost from LiteLLM's built-in cost calculation
    - Duration (start_time, end_time)
    - Model used (including fallback detection)
    - Token usage
    - Errors and failures

    This supplements (and can eventually replace) the manual instrumentation
    in open_ai/utils_new.py.
    """

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called after a successful LiteLLM API call."""
        try:
            model = kwargs.get("model", "unknown")
            call_type = kwargs.get("call_type", "completion")
            duration = (
                (end_time - start_time).total_seconds()
                if start_time and end_time
                else 0
            )

            # Extract cost from LiteLLM's built-in calculation
            cost = 0.0
            hidden = getattr(response_obj, "_hidden_params", None) or {}
            if hidden:
                cost = hidden.get("response_cost", 0.0) or 0.0

            # Extract usage
            usage_info = {}
            if hasattr(response_obj, "usage") and response_obj.usage:
                usage = response_obj.usage
                usage_info = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }

            cache_hit = hidden.get("cache_hit", False) if hidden else False

            logger.debug(
                "LiteLLM %s success: model=%s, duration=%.2fs, cost=$%.6f, "
                "tokens=%s, cache_hit=%s",
                call_type,
                model,
                duration,
                cost,
                usage_info.get("total_tokens", 0),
                cache_hit,
            )

            # Silent-200 upstream signals. LiteLLM doesn't convert any of these
            # to exceptions — the call "succeeds" even though the provider
            # refused, truncated, filtered, or returned nothing. Surface them
            # as warnings so they're queryable in Loki instead of invisible.
            self._warn_on_silent_signals(kwargs, response_obj, model, call_type)

        except Exception:
            logger.debug(
                "Error in MagnetAILogger.async_log_success_event", exc_info=True
            )

    def _warn_on_silent_signals(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        model: str,
        call_type: str,
    ) -> None:
        """Detect upstream refusals / truncation / filters / guardrails on a 200."""
        choices = getattr(response_obj, "choices", None) or []
        c0 = choices[0] if choices else None
        msg = getattr(c0, "message", None) if c0 else None

        finish = getattr(c0, "finish_reason", None) if c0 else None
        psf = (getattr(c0, "provider_specific_fields", None) or {}) if c0 else {}
        native_finish = (
            psf.get("native_finish_reason") if isinstance(psf, dict) else None
        )
        refusal = getattr(msg, "refusal", None) if msg else None
        content = getattr(msg, "content", None) if msg else None
        tool_calls = getattr(msg, "tool_calls", None) if msg else None

        if finish == "content_filter" or refusal:
            logger.warning(
                "LiteLLM upstream refusal: model=%s, call_type=%s, finish=%s, "
                "native_finish=%s, refusal=%s",
                model,
                call_type,
                finish,
                native_finish,
                str(refusal)[:300] if refusal else None,
            )
        elif finish == "length":
            logger.warning(
                "LiteLLM upstream truncation: model=%s, call_type=%s, "
                "completion_tokens=%s",
                model,
                call_type,
                getattr(
                    getattr(response_obj, "usage", None), "completion_tokens", None
                ),
            )
        elif (
            finish == "stop"
            and call_type == "completion"
            and not content
            and not tool_calls
        ):
            logger.warning(
                "LiteLLM upstream empty completion: model=%s, finish=%s",
                model,
                finish,
            )

        # Azure prompt/content filter on a 200
        pfr = getattr(response_obj, "prompt_filter_results", None)
        cfr = getattr(c0, "content_filter_results", None) if c0 else None
        if pfr or cfr:
            logger.warning(
                "LiteLLM Azure content filter (200): model=%s, "
                "prompt_filter=%s, content_filter=%s",
                model,
                pfr,
                cfr,
            )

        # Guardrail intervention (proxy path — no-op in SDK-only mode)
        slo = kwargs.get("standard_logging_object") or {}
        status_fields = (
            (slo.get("status_fields") or {}) if isinstance(slo, dict) else {}
        )
        gs = status_fields.get("guardrail_status")
        if gs and gs not in (None, "success", "not_run"):
            meta = slo.get("metadata") or {} if isinstance(slo, dict) else {}
            logger.warning(
                "LiteLLM guardrail intervened: model=%s, status=%s, info=%s",
                model,
                gs,
                meta.get("guardrail_information"),
            )

        # Rate-limit headroom depleted (next call will 429)
        hidden = getattr(response_obj, "_hidden_params", None) or {}
        headers = hidden.get("additional_headers") or {}
        if isinstance(headers, dict):
            rem_req = headers.get("x_ratelimit_remaining_requests")
            rem_tok = headers.get("x_ratelimit_remaining_tokens")
            try:
                if (rem_req is not None and int(rem_req) == 0) or (
                    rem_tok is not None and int(rem_tok) == 0
                ):
                    logger.warning(
                        "LiteLLM upstream ratelimit depleted: model=%s, "
                        "remaining_requests=%s, remaining_tokens=%s",
                        model,
                        rem_req,
                        rem_tok,
                    )
            except (TypeError, ValueError):
                pass

    async def async_log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called after a failed LiteLLM API call."""
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

            # Classify origin: LiteLLM-internal errors ship a stub httpx
            # response whose request URL is `https://litellm.ai` (see
            # litellm/litellm_core_utils/exception_mapping_utils.py). Upstream
            # errors carry a real provider URL. `llm_provider` and
            # `status_code` are set by LiteLLM's exception mapper only when the
            # error crossed the wire. We use these three signals together so
            # the log line answers "was it us or them?" at a glance.
            status_code: int | None = None
            llm_provider: str | None = None
            num_retries: int | None = None
            max_retries: int | None = None
            upstream_url: str | None = None
            origin = "unknown"
            if exception is not None:
                status_code = getattr(exception, "status_code", None)
                llm_provider = getattr(exception, "llm_provider", None) or None
                num_retries = getattr(exception, "num_retries", None)
                max_retries = getattr(exception, "max_retries", None)
                resp = getattr(exception, "response", None)
                request = getattr(resp, "request", None) if resp else None
                raw_url = getattr(request, "url", None) if request else None
                upstream_url = str(raw_url) if raw_url else None
                if upstream_url and "litellm.ai" not in upstream_url:
                    origin = "upstream"
                elif status_code and status_code >= 400 and llm_provider:
                    origin = "upstream"
                else:
                    origin = "litellm"

            # Cooldown signals: LiteLLM's Router raises these when a deployment
            # is circuit-broken. Upgrading them to WARNING (not ERROR) so they
            # show up in Loki as `logger="services.ai_services.callbacks"` and
            # are easy to filter on (see BACKEND_FIXES_ROADMAP.md §C.2).
            cooldown_markers = (
                "is currently cooling down",
                "No deployments available",
                "allowed_fails",
            )
            if error_str and any(marker in error_str for marker in cooldown_markers):
                logger.warning(
                    "LiteLLM cooldown hit: model=%s, call_type=%s, "
                    "num_retries=%s, error=%s",
                    model,
                    call_type,
                    num_retries,
                    error_str,
                )
                return

            logger.error(
                "LiteLLM %s failure: model=%s, duration=%.2fs, origin=%s, "
                "error_type=%s, status=%s, llm_provider=%s, "
                "retries=%s/%s, upstream_url=%s, error=%s",
                call_type,
                model,
                duration,
                origin,
                error_type,
                status_code,
                llm_provider,
                num_retries,
                max_retries,
                upstream_url,
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
        """Called after a streaming LiteLLM call completes."""
        # Delegate to success handler — streaming events have similar structure
        await self.async_log_success_event(kwargs, response_obj, start_time, end_time)
