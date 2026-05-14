"""In-memory webhook rate limit tests (P2-4).

Pins the contract: 60 events/min per key, sliding window, per-process.
"""

from __future__ import annotations

import pytest

from services.agents.teams.webhook_rate_limit import (
    MAX_EVENTS_PER_MINUTE,
    allow,
    reset_for_tests,
)


@pytest.fixture(autouse=True)
async def _clear():
    await reset_for_tests()
    yield
    await reset_for_tests()


@pytest.mark.asyncio
async def test_first_request_allowed():
    assert await allow("k1") is True


@pytest.mark.asyncio
async def test_burst_up_to_cap_allowed():
    for _ in range(MAX_EVENTS_PER_MINUTE):
        assert await allow("k2") is True


@pytest.mark.asyncio
async def test_over_cap_denied():
    for _ in range(MAX_EVENTS_PER_MINUTE):
        await allow("k3")
    assert await allow("k3") is False


@pytest.mark.asyncio
async def test_keys_isolated():
    for _ in range(MAX_EVENTS_PER_MINUTE):
        await allow("ka")
    # Other key still has full budget.
    assert await allow("kb") is True


@pytest.mark.asyncio
async def test_old_timestamps_evicted():
    """Timestamps older than the 60s window don't count against the cap."""
    # Stuff the bucket at an old timestamp.
    for _ in range(MAX_EVENTS_PER_MINUTE):
        assert await allow("k4", now=0.0) is True
    # 61s later we should have full budget again.
    assert await allow("k4", now=61.0) is True


@pytest.mark.asyncio
async def test_sliding_window_partial_eviction():
    # Fill bucket at t=0..t=29 (30 hits), then half the bucket at t=40..t=69.
    for i in range(30):
        await allow("k5", now=float(i))
    for i in range(30):
        await allow("k5", now=40.0 + i)
    # At t=61.0 the first half (timestamps 0..0.99) is evicted, second half
    # (timestamps 40..69) remains. We've used 30 of 60 slots in the live
    # window, so one more should still be allowed.
    assert await allow("k5", now=61.0) is True
