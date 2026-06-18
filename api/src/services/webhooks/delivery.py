"""Outbound webhook delivery for agent replies.

Used by webhook-driven (async) agent invocation: once a turn produces a reply,
the reply is POSTed to the caller-supplied callback URL. Bodies are signed with
HMAC-SHA256 over the exact bytes sent, under the ``X-Magnet-Signature`` header
(``sha256=<hexdigest>``), using the shared ``AGENT_WEBHOOK_SIGNING_SECRET``.
The receiver recomputes the signature over the raw body to authenticate us.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from core.config.base import get_webhook_settings

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-Magnet-Signature"


def sign_payload(body: bytes, secret: str) -> str:
    """Return the ``sha256=<hexdigest>`` HMAC signature for ``body``."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


class _RetryableStatus(Exception):
    """Raised for 5xx/429 responses so tenacity retries them."""


async def deliver_agent_reply(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> bool:
    """Deliver ``payload`` to ``url`` with retries. Returns True on 2xx.

    Network errors and retryable status codes (429, 5xx) are retried with
    exponential backoff up to ``AGENT_WEBHOOK_MAX_ATTEMPTS``. 4xx (other than
    429) are treated as permanent and not retried.
    """
    settings = get_webhook_settings()
    # Serialize once so the signature matches the exact bytes we transmit.
    body = httpx.Request("POST", url, json=payload).content

    request_headers: dict[str, str] = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    if settings.SIGNING_SECRET:
        request_headers[SIGNATURE_HEADER] = sign_payload(body, settings.SIGNING_SECRET)
    else:
        logger.warning(
            "AGENT_WEBHOOK_SIGNING_SECRET is not set; delivering callback unsigned"
        )

    attempts = max(1, settings.MAX_ATTEMPTS)

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential_jitter(initial=0.5, max=10),
            retry=retry_if_exception_type((httpx.TransportError, _RetryableStatus)),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(
                    timeout=settings.TIMEOUT_SECONDS
                ) as client:
                    response = await client.post(
                        url, content=body, headers=request_headers
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    raise _RetryableStatus(f"retryable status {response.status_code}")
                if response.status_code >= 400:
                    logger.error(
                        "Webhook callback to %s rejected with status %s (no retry)",
                        url,
                        response.status_code,
                    )
                    return False
                logger.info(
                    "Delivered agent reply webhook to %s (status %s)",
                    url,
                    response.status_code,
                )
                return True
    except Exception:
        logger.exception("Failed to deliver agent reply webhook to %s", url)
        return False

    return False
