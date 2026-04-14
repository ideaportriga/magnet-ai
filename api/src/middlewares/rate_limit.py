"""Simple in-memory rate limiter for authentication endpoints.

Uses a sliding-window counter per IP address.  Suitable for single-instance
deployments; for multi-instance, swap the dict for a shared store (Redis).
"""

from __future__ import annotations

import time
from collections import defaultdict
from logging import getLogger
from typing import Final

from litestar.connection import ASGIConnection
from litestar.exceptions import TooManyRequestsException

logger = getLogger(__name__)

# {path_prefix: (max_requests, window_seconds)}
_RATE_LIMITS: Final[dict[str, tuple[int, int]]] = {
    "/api/v2/auth/login": (10, 60),  # 10 attempts per minute
    "/api/v2/auth/signup": (5, 3600),  # 5 per hour
    "/api/v2/auth/password/forgot": (5, 300),  # 5 per 5 minutes
    "/api/v2/auth/mfa/verify": (10, 300),  # 10 per 5 minutes
}

# {(ip, path_prefix): list[timestamps]}
_REQUESTS: dict[tuple[str, str], list[float]] = defaultdict(list)

# Periodic cleanup: max number of keys before a full sweep removes stale entries
_MAX_KEYS_BEFORE_SWEEP: Final[int] = 10_000
_MAX_WINDOW: Final[int] = max(window for _, window in _RATE_LIMITS.values())


def _get_client_ip(connection: ASGIConnection) -> str:
    """Extract client IP, respecting X-Forwarded-For behind reverse proxy."""
    forwarded = connection.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = connection.scope.get("client")
    return client[0] if client else "unknown"


def _sweep_stale_entries(now: float) -> None:
    """Remove keys whose timestamps have all expired (prevents memory leak)."""
    cutoff = now - _MAX_WINDOW
    stale_keys = [k for k, ts in _REQUESTS.items() if not ts or ts[-1] <= cutoff]
    for k in stale_keys:
        del _REQUESTS[k]


def check_rate_limit(connection: ASGIConnection) -> None:
    """Check rate limit for the current request. Raise 429 if exceeded."""
    path = connection.scope.get("path", "")

    for prefix, (max_requests, window) in _RATE_LIMITS.items():
        if path.startswith(prefix):
            break
    else:
        return  # No rate limit for this path

    ip = _get_client_ip(connection)
    key = (ip, prefix)
    now = time.monotonic()

    # Periodic sweep to reclaim memory from IPs that stopped making requests
    if len(_REQUESTS) > _MAX_KEYS_BEFORE_SWEEP:
        _sweep_stale_entries(now)

    # Prune expired entries for this key
    timestamps = _REQUESTS[key]
    cutoff = now - window
    _REQUESTS[key] = timestamps = [t for t in timestamps if t > cutoff]

    if len(timestamps) >= max_requests:
        logger.warning(
            "Rate limit exceeded: ip=%s path=%s (%d/%d in %ds)",
            ip,
            prefix,
            len(timestamps),
            max_requests,
            window,
        )
        raise TooManyRequestsException(
            detail="Too many requests. Please try again later."
        )

    timestamps.append(now)
