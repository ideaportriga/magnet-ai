"""Registry for background tasks spawned from request handlers.

Usage in route handlers:

    from core.server.background_tasks import spawn_background_task

    spawn_background_task(my_async_func(arg1, arg2), name="sync-source-42")

On shutdown the registry awaits all pending tasks (with a timeout).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Coroutine

logger = logging.getLogger(__name__)

_active_tasks: set[asyncio.Task] = set()

# Counters for monitoring (exposed via /health endpoint and available for OTLP)
_completed_count: int = 0
_failed_count: int = 0
_cancelled_count: int = 0


def spawn_background_task(
    coro: Coroutine[Any, Any, Any],
    *,
    name: str | None = None,
) -> asyncio.Task:
    """Create a tracked background task.

    The task is automatically removed from the registry when it finishes.
    Exceptions are logged but not re-raised.
    """
    task = asyncio.create_task(coro, name=name)
    _active_tasks.add(task)
    task.add_done_callback(_task_done)
    return task


def _task_done(task: asyncio.Task) -> None:
    global _completed_count, _failed_count, _cancelled_count
    _active_tasks.discard(task)
    if task.cancelled():
        _cancelled_count += 1
        logger.debug("Background task %s was cancelled", task.get_name())
        return
    exc = task.exception()
    if exc:
        _failed_count += 1
        logger.error(
            "Background task %s failed: %s",
            task.get_name(),
            exc,
            exc_info=exc,
        )
    else:
        _completed_count += 1


def active_task_count() -> int:
    """Return the number of currently running background tasks."""
    return len(_active_tasks)


def task_stats() -> dict[str, int]:
    """Return background task counters for monitoring."""
    return {
        "active": len(_active_tasks),
        "completed": _completed_count,
        "failed": _failed_count,
        "cancelled": _cancelled_count,
    }


async def shutdown_background_tasks(shutdown_timeout: float = 30.0) -> None:
    """Wait for all background tasks to finish, then cancel stragglers.

    Called during application shutdown.
    """
    if not _active_tasks:
        return

    pending = list(_active_tasks)
    logger.info(
        "Waiting for %d background task(s) to finish (timeout=%.0fs)",
        len(pending),
        shutdown_timeout,
    )

    done, still_pending = await asyncio.wait(pending, timeout=shutdown_timeout)

    if still_pending:
        logger.warning(
            "Cancelling %d background task(s) that didn't finish in time",
            len(still_pending),
        )
        for task in still_pending:
            task.cancel()
        await asyncio.gather(*still_pending, return_exceptions=True)

    logger.info("All background tasks finished")
