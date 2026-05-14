"""Error classification for the webhook → STT pipeline.

The worker that drives ``process_teams_recording_notification_bg_task``
needs to choose between:

* **retry later** — transient Graph 5xx, network blip, read timeout. The
  recording will still be there; we wait and try again.
* **fail and surface to user** — the meeting organizer's delegated token
  has expired or was revoked. Retrying won't help, only re-auth will.
  Notify the chat once and stop.
* **fail and stop** — non-recoverable client errors (404, malformed
  notification, etc.). Mark the event failed; do not spam retries.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-4.
"""

from __future__ import annotations

import asyncio
from typing import Literal

import httpx

Classification = Literal["transient", "unauthorized", "permanent"]


class WebhookProcessingError(Exception):
    """Marker base — let the worker pick a retry strategy."""

    classification: Classification = "permanent"

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class TransientWebhookError(WebhookProcessingError):
    """Retry-able — Graph 5xx, network timeout, read errors."""

    classification = "transient"


class UnauthorizedWebhookError(WebhookProcessingError):
    """Delegated token expired or revoked. User must re-authorize."""

    classification = "unauthorized"


class PermanentWebhookError(WebhookProcessingError):
    """Non-recoverable client error — mark failed and stop."""

    classification = "permanent"


_TRANSIENT_HTTP_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
_UNAUTHORIZED_HTTP_STATUSES = frozenset({401, 403})


def classify_exception(err: BaseException) -> Classification:
    """Return the retry policy bucket for a raw exception.

    Anything that looks like a network hiccup is transient; HTTP 401/403
    are unauthorized; the rest defaults to permanent.
    """
    if isinstance(
        err, (asyncio.TimeoutError, httpx.TimeoutException, httpx.NetworkError)
    ):
        return "transient"
    if isinstance(err, httpx.HTTPStatusError):
        status = err.response.status_code if err.response is not None else 0
        if status in _UNAUTHORIZED_HTTP_STATUSES:
            return "unauthorized"
        if status in _TRANSIENT_HTTP_STATUSES:
            return "transient"
        return "permanent"
    return "permanent"


def wrap_classified(err: BaseException, *, message: str) -> WebhookProcessingError:
    """Return a typed wrapper carrying the classification."""
    cls_map = {
        "transient": TransientWebhookError,
        "unauthorized": UnauthorizedWebhookError,
        "permanent": PermanentWebhookError,
    }
    bucket = classify_exception(err)
    return cls_map[bucket](message, cause=err)
