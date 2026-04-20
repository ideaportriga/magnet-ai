"""Background task that logs asyncio event-loop lag.

Early warning signal for scheduler hangs: APScheduler 3.x ran sync jobstore
I/O inside the event loop, and a half-open TCP connection could freeze the
whole API for 30+ seconds. This monitor sleeps for a fixed interval and
compares real elapsed time — if the wake-up is later than expected, some
coroutine held the loop. See BACKEND_FIXES_ROADMAP.md §B.5.
"""

from __future__ import annotations

import asyncio
import time
from logging import getLogger

logger = getLogger(__name__)

_SLEEP_SECONDS = 1.0
_WARN_THRESHOLD_SECONDS = 0.5


async def _monitor_event_loop_lag() -> None:
    while True:
        try:
            start = time.monotonic()
            await asyncio.sleep(_SLEEP_SECONDS)
            lag = time.monotonic() - start - _SLEEP_SECONDS
            if lag > _WARN_THRESHOLD_SECONDS:
                logger.warning(
                    "Event loop lag detected: %.3fs (threshold %.3fs)",
                    lag,
                    _WARN_THRESHOLD_SECONDS,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            # The monitor must never die — it's our last line of visibility.
            logger.exception("Event loop monitor iteration failed")
            await asyncio.sleep(_SLEEP_SECONDS)


def start_event_loop_monitor() -> asyncio.Task[None]:
    """Start the monitor as a detached task. Returns the task for cancellation on shutdown."""
    loop = asyncio.get_event_loop()
    return loop.create_task(_monitor_event_loop_lag(), name="event-loop-lag-monitor")
