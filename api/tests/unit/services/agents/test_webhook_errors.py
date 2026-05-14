"""Webhook error classifier tests.

Pins the retry policy buckets used by
``tasks/definitions/background.py::process_teams_recording_notification_bg_task``:

* 401/403 → unauthorized (don't retry, notify user once)
* 5xx / timeout / network → transient (retry with backoff)
* everything else → permanent (mark failed)

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-4.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from services.agents.teams.webhook_errors import (
    PermanentWebhookError,
    TransientWebhookError,
    UnauthorizedWebhookError,
    classify_exception,
    wrap_classified,
)


def _http_error(status: int) -> httpx.HTTPStatusError:
    class _FakeResp:
        status_code = status

    return httpx.HTTPStatusError(f"HTTP {status}", request=None, response=_FakeResp())


@pytest.mark.parametrize("status", [401, 403])
def test_unauthorized_statuses(status):
    assert classify_exception(_http_error(status)) == "unauthorized"


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
def test_transient_statuses(status):
    assert classify_exception(_http_error(status)) == "transient"


@pytest.mark.parametrize("status", [400, 404, 410, 422])
def test_permanent_statuses(status):
    assert classify_exception(_http_error(status)) == "permanent"


def test_timeout_is_transient():
    assert classify_exception(asyncio.TimeoutError()) == "transient"


def test_httpx_timeout_is_transient():
    assert classify_exception(httpx.ReadTimeout("read timeout")) == "transient"


def test_network_error_is_transient():
    assert classify_exception(httpx.ConnectError("conn refused")) == "transient"


def test_value_error_is_permanent():
    assert classify_exception(ValueError("bad input")) == "permanent"


def test_wrap_classified_returns_typed():
    assert isinstance(
        wrap_classified(_http_error(401), message="x"), UnauthorizedWebhookError
    )
    assert isinstance(
        wrap_classified(_http_error(503), message="x"), TransientWebhookError
    )
    assert isinstance(
        wrap_classified(_http_error(404), message="x"), PermanentWebhookError
    )
    assert isinstance(
        wrap_classified(ValueError("x"), message="x"), PermanentWebhookError
    )


def test_wrap_carries_cause():
    cause = _http_error(503)
    wrapped = wrap_classified(cause, message="boom")
    assert wrapped.__cause__ is cause
    assert str(wrapped) == "boom"
    assert wrapped.classification == "transient"
