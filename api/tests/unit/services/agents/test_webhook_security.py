"""Regression tests for the Graph webhook clientState resolver.

Covers the contract documented in
``services.agents.teams.webhook_security`` and called out in
``docs/NOTE_TAKER_RELIABILITY_PLAN.md`` § P0-3:

* The published default ``"recordings-ready"`` is never accepted.
* Production with no/weak secret fails fast.
* Non-production with no secret generates a random per-process fallback.
* The resolver is memoized.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from services.agents.teams.webhook_security import (
    ENV_VAR,
    InsecureWebhookClientStateError,
    get_graph_webhook_client_state,
    reset_cache_for_tests,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache_for_tests()
    yield
    reset_cache_for_tests()


def _env(**overrides: str | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {ENV_VAR, "ENVIRONMENT"}}
    for k, v in overrides.items():
        if v is not None:
            env[k] = v
    return env


def test_accepts_strong_secret_in_production():
    secret = "x" * 64
    with patch.dict(
        os.environ,
        _env(ENVIRONMENT="production", **{ENV_VAR: secret}),
        clear=True,
    ):
        assert get_graph_webhook_client_state() == secret


def test_rejects_published_default_in_production():
    with patch.dict(
        os.environ,
        _env(ENVIRONMENT="production", **{ENV_VAR: "recordings-ready"}),
        clear=True,
    ):
        with pytest.raises(InsecureWebhookClientStateError):
            get_graph_webhook_client_state()


def test_rejects_published_default_in_dev_but_falls_back():
    with patch.dict(
        os.environ,
        _env(ENVIRONMENT="development", **{ENV_VAR: "recordings-ready"}),
        clear=True,
    ):
        value = get_graph_webhook_client_state()
        assert value != "recordings-ready"
        assert len(value) >= 32


def test_missing_env_fails_in_production():
    with patch.dict(os.environ, _env(ENVIRONMENT="production"), clear=True):
        with pytest.raises(InsecureWebhookClientStateError):
            get_graph_webhook_client_state()


def test_missing_env_generates_fallback_in_dev():
    with patch.dict(os.environ, _env(ENVIRONMENT="development"), clear=True):
        value = get_graph_webhook_client_state()
        assert len(value) >= 32


def test_short_secret_fails_in_production():
    with patch.dict(
        os.environ,
        _env(ENVIRONMENT="production", **{ENV_VAR: "short"}),
        clear=True,
    ):
        with pytest.raises(InsecureWebhookClientStateError):
            get_graph_webhook_client_state()


def test_short_secret_warns_but_accepts_in_dev():
    with patch.dict(
        os.environ,
        _env(ENVIRONMENT="development", **{ENV_VAR: "short"}),
        clear=True,
    ):
        assert get_graph_webhook_client_state() == "short"


def test_result_is_memoized():
    with patch.dict(os.environ, _env(ENVIRONMENT="development"), clear=True):
        first = get_graph_webhook_client_state()
        second = get_graph_webhook_client_state()
        assert first == second


def test_cache_can_be_reset_for_tests():
    with patch.dict(os.environ, _env(ENVIRONMENT="development"), clear=True):
        first = get_graph_webhook_client_state()
        reset_cache_for_tests()
        second = get_graph_webhook_client_state()
        assert first != second
