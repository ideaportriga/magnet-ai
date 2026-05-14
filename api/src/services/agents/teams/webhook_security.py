"""Security helpers for the Microsoft Graph webhook flow.

The Graph subscription protocol echoes back a ``clientState`` field on every
notification. We rely on it as a shared-secret check, so the value must be
unguessable in production. The historical default — the literal string
``"recordings-ready"`` — was published in the codebase and is therefore
unsafe; this module is the single source of truth for resolving the secret
and refuses to fall back to that value when the environment looks like prod.

Resolution rules:

* ``TEAMS_GRAPH_WEBHOOK_CLIENT_STATE`` env var, when set to a non-empty,
  non-default value, wins. Length below :data:`_MIN_LENGTH` is rejected in
  production (warning in dev so local devs aren't blocked).
* If the env var is missing/empty/insecure and ``ENVIRONMENT=production`` —
  raise :class:`InsecureWebhookClientStateError`. The webhook handlers
  surface this as a 500 and abort subscription creation.
* In non-production environments we generate a random per-process value the
  first time someone asks, logging a loud warning. This keeps unit tests and
  local Teams flows working without forcing devs to manage a secret, while
  ensuring nothing accidentally matches a real Graph subscription.
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from logging import getLogger

logger = getLogger(__name__)

ENV_VAR = "TEAMS_GRAPH_WEBHOOK_CLIENT_STATE"

_MIN_LENGTH = 32

# Values that have appeared as published defaults at any point in the
# codebase. Treat them as compromised — never accept them, even if they
# happen to be re-set via env.
_INSECURE_DEFAULTS: frozenset[str] = frozenset({"recordings-ready"})


class InsecureWebhookClientStateError(RuntimeError):
    """Raised when no safe value can be resolved in production."""


def _is_production() -> bool:
    return (os.environ.get("ENVIRONMENT") or "").strip().lower() == "production"


@lru_cache(maxsize=1)
def get_graph_webhook_client_state() -> str:
    """Return the secret to embed in Graph subscriptions and verify on webhook.

    Memoized — generation happens at most once per process.
    """
    raw = (os.environ.get(ENV_VAR) or "").strip()
    in_prod = _is_production()

    if raw in _INSECURE_DEFAULTS:
        message = (
            f"{ENV_VAR} is set to a known-published default value; refusing to use it."
        )
        if in_prod:
            raise InsecureWebhookClientStateError(message)
        logger.warning("%s Generating a per-process fallback (dev only).", message)
        raw = ""

    if not raw:
        if in_prod:
            raise InsecureWebhookClientStateError(
                f"{ENV_VAR} must be set to a strong secret (>= {_MIN_LENGTH} chars) "
                "in production. Set it on the deployment before creating Graph "
                "subscriptions."
            )
        generated = secrets.token_urlsafe(32)
        logger.warning(
            "%s is not set; using a randomly generated per-process value. "
            "This will not match any real Graph subscription — set the env var "
            "for any environment that receives webhooks from Microsoft Graph.",
            ENV_VAR,
        )
        return generated

    if len(raw) < _MIN_LENGTH:
        message = f"{ENV_VAR} is shorter than the recommended {_MIN_LENGTH} characters."
        if in_prod:
            raise InsecureWebhookClientStateError(
                message + " Refusing to start in production with a weak webhook secret."
            )
        logger.warning("%s Accepting anyway (non-production).", message)

    return raw


def reset_cache_for_tests() -> None:
    """Clear the memoized value. Tests only."""
    get_graph_webhook_client_state.cache_clear()
