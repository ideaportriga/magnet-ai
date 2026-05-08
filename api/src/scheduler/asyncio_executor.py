"""Thread-safe AsyncIO executor for APScheduler.

Stock `apscheduler.executors.asyncio.AsyncIOExecutor._do_submit_job` calls
`self._eventloop.create_task(coro)` / `self._eventloop.run_in_executor(...)`,
both of which are not thread-safe — they must be invoked from the event
loop's own thread.  `scheduler.manager._patch_scheduler_wakeup` offloads
`_process_jobs()` to a worker thread so synchronous SQLAlchemyJobStore
calls don't block the event loop, which means `submit_job()` ends up
running in a worker thread.  When that happens the stock executor leaks
the task — it's created but never registered with the loop's ready
queue — and surfaces as `Task was destroyed but it is pending!` /
`coroutine 'run_coroutine_job' was never awaited`.

This subclass uses `asyncio.run_coroutine_threadsafe`, the documented
API for scheduling a coroutine onto an event loop from another thread.
It returns `concurrent.futures.Future`, which APScheduler treats
interchangeably with `asyncio.Future` (same `add_done_callback`,
`cancel`, `result`, `exception`, `done` surface).
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.base import run_coroutine_job, run_job
from apscheduler.util import iscoroutinefunction_partial


class ThreadSafeAsyncIOExecutor(AsyncIOExecutor):
    """`AsyncIOExecutor` whose `submit_job()` is callable from any thread."""

    def _do_submit_job(self, job: Any, run_times: list) -> None:
        def callback(f: Any) -> None:
            self._pending_futures.discard(f)
            try:
                events = f.result()
            except BaseException:
                self._run_job_error(job.id, *sys.exc_info()[1:])
            else:
                self._run_job_success(job.id, events)

        if iscoroutinefunction_partial(job.func):
            coro = run_coroutine_job(
                job, job._jobstore_alias, run_times, self._logger.name
            )
            future = asyncio.run_coroutine_threadsafe(coro, self._eventloop)
        else:

            async def _run_sync_in_default_executor() -> Any:
                return await self._eventloop.run_in_executor(
                    None,
                    run_job,
                    job,
                    job._jobstore_alias,
                    run_times,
                    self._logger.name,
                )

            future = asyncio.run_coroutine_threadsafe(
                _run_sync_in_default_executor(), self._eventloop
            )

        future.add_done_callback(callback)
        self._pending_futures.add(future)
