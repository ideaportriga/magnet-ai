"""In-memory rate limiter for Graph webhook ingress.

Each incoming webhook gets a stable key (per-subscription_id when we
can extract it, falling back to the source IP). We allow
:data:`MAX_EVENTS_PER_MINUTE` keyed events per minute; anything past
that is dropped with a 429. The window slides naturally because
timestamps older than 60s are evicted on every check.

This is deliberately a process-local limiter rather than a Redis-backed
one — webhook abuse this matters for would already be filtered by the
``clientState`` check; rate limiting is the second line of defence
against an attacker who's stolen / guessed the secret. The fleet-wide
"true" limit ends up larger than what any single attacker can produce
against one pod, so the per-process cap still cuts the worst-case load
by a meaningful factor.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P2-4.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from logging import getLogger
from typing import Deque

logger = getLogger(__name__)

MAX_EVENTS_PER_MINUTE = 60
_WINDOW_SECONDS = 60.0

_buckets: dict[str, Deque[float]] = {}
_lock = asyncio.Lock()


async def allow(key: str, *, now: float | None = None) -> bool:
    """Return True if a hit at ``now`` (default: monotonic clock) is within budget.

    The bucket for ``key`` retains timestamps younger than 60s; if the
    bucket would exceed :data:`MAX_EVENTS_PER_MINUTE` after the new
    timestamp, the call returns ``False`` and nothing is appended.

    Callers should treat ``False`` as "drop the event" — for a webhook
    handler that's a 429 response.
    """
    ts = time.monotonic() if now is None else now
    cutoff = ts - _WINDOW_SECONDS
    async with _lock:
        bucket = _buckets.get(key)
        if bucket is None:
            bucket = deque()
            _buckets[key] = bucket
        # Evict expired timestamps.
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= MAX_EVENTS_PER_MINUTE:
            return False
        bucket.append(ts)
        return True


async def reset_for_tests() -> None:
    """Clear all buckets. Tests only."""
    async with _lock:
        _buckets.clear()
