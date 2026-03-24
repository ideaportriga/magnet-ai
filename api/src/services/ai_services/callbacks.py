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
            if hasattr(response_obj, "_hidden_params"):
                cost = response_obj._hidden_params.get("response_cost", 0.0)

            # Extract usage
            usage_info = {}
            if hasattr(response_obj, "usage") and response_obj.usage:
                usage = response_obj.usage
                usage_info = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }

            # Check for cache hit
            cache_hit = False
            if hasattr(response_obj, "_hidden_params"):
                cache_hit = response_obj._hidden_params.get("cache_hit", False)

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

            logger.error(
                "LiteLLM %s failure: model=%s, duration=%.2fs, error_type=%s, error=%s",
                call_type,
                model,
                duration,
                error_type,
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
