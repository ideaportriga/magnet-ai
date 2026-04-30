"""In-process TaskIQ worker + scheduler runtime.

Spawns `taskiq.api.run_receiver_task` (worker) and
`taskiq.api.run_scheduler_task` (scheduler) as asyncio tasks inside the
Litestar event loop. Lets us run API + worker + scheduler in a single
Container Apps replica without a process supervisor — the trade-off vs.
multi-container is documented in `docs/PRODUCTION_TASKIQ_DEPLOYMENT_PLAN.md`.

Lifecycle ordering (relies on plugin registration order in
`core/server/plugin_registry.py`):

1. `StartupPlugin._startup_taskiq_broker` runs → `broker.startup()` fires
   `CLIENT_STARTUP` and creates asyncpg pools.
2. `TaskiqRuntimePlugin._start_runtime` runs → seeds worker-side resources
   via `setup_worker_runtime(share_with_litestar=True)`, flips
   `broker.is_worker_process = True`, then spawns the receiver / scheduler
   tasks with `run_startup=False` so the broker is NOT re-initialised.
3. On shutdown, `TaskiqRuntimePlugin._stop_runtime` cancels the tasks,
   awaits them (bounded by `TASKIQ_WAIT_TASKS_TIMEOUT` so SIGTERM doesn't
   hang forever), then `ShutdownPlugin._shutdown_taskiq_broker` closes
   pools.

Why we don't pass `run_startup=True` to taskiq's helpers: that would re-run
`broker.startup()`, leaking the asyncpg pools created in step 1 and
re-firing `CLIENT_STARTUP` handlers. Instead we set `is_worker_process`
ourselves and call the worker init directly via
`tasks.worker_lifecycle.setup_worker_runtime`.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Litestar
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


_WORKER_TASK_ATTR = "taskiq_worker_task"
_SCHEDULER_TASK_ATTR = "taskiq_scheduler_task"


class TaskiqRuntimePlugin(InitPluginProtocol):
    """Plugin that runs TaskIQ worker + scheduler in the API event loop."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        # Append to startup so we run AFTER `StartupPlugin._startup_taskiq_broker`.
        app_config.on_startup = [*(app_config.on_startup or []), self._start_runtime]
        # Insert at the FRONT of shutdown so we cancel taskiq tasks BEFORE
        # `ShutdownPlugin._shutdown_taskiq_broker` closes the asyncpg pools
        # the receiver is still using.
        app_config.on_shutdown = [self._stop_runtime, *(app_config.on_shutdown or [])]
        return app_config

    async def _start_runtime(self, app: Litestar) -> None:
        from core.config.base import get_settings

        settings = get_settings().taskiq

        worker_enabled = settings.TASKIQ_INPROCESS_WORKER_ENABLED
        scheduler_enabled = settings.TASKIQ_INPROCESS_SCHEDULER_ENABLED

        if not worker_enabled and not scheduler_enabled:
            logger.info(
                "TaskiqRuntimePlugin: both in-process worker and scheduler "
                "disabled, nothing to do"
            )
            return

        broker = getattr(app.state, "taskiq_broker", None)
        if broker is None:
            logger.error(
                "TaskiqRuntimePlugin: broker not on app.state — was the "
                "StartupPlugin registered before this plugin?"
            )
            return

        if worker_enabled:
            await self._spawn_worker(app, broker, settings)

        if scheduler_enabled:
            await self._spawn_scheduler(app, settings)

    async def _spawn_worker(self, app: Litestar, broker, settings) -> None:
        from taskiq.acks import AcknowledgeType
        from taskiq.api import run_receiver_task

        from tasks.worker_lifecycle import setup_worker_runtime

        # Worker init normally runs inside `broker.startup()` via the
        # WORKER_STARTUP event. In-process the broker is already started in
        # CLIENT mode, so we run the init manually with the shared-litestar
        # flag (DB engines / storage are owned by Litestar plugins).
        await setup_worker_runtime(broker.state, share_with_litestar=True)

        # Receiver checks `broker.is_worker_process` to flag itself; flipping
        # it here also makes any future broker.shutdown() call fire
        # WORKER_SHUTDOWN handlers — which is fine, our handlers are now
        # idempotent against a Litestar-owned engine.
        broker.is_worker_process = True

        worker_task = asyncio.create_task(
            run_receiver_task(
                broker,
                max_async_tasks=settings.TASKIQ_WORKER_CONCURRENCY,
                ack_time=AcknowledgeType.WHEN_EXECUTED,
                run_startup=False,
            ),
            name="taskiq_in_process_worker",
        )
        worker_task.add_done_callback(self._on_runtime_task_done)
        setattr(app.state, _WORKER_TASK_ATTR, worker_task)
        logger.info(
            "TaskIQ in-process worker started (concurrency=%d)",
            settings.TASKIQ_WORKER_CONCURRENCY,
        )

    async def _spawn_scheduler(self, app: Litestar, settings) -> None:
        from taskiq.api import run_scheduler_task

        from tasks import scheduler

        # `run_scheduler_task` calls `await source.startup()` for every
        # source on the scheduler — for our PreservingAsyncpgScheduleSource
        # this creates the asyncpg pool and upserts static schedules,
        # leaving dynamic rows untouched. Safe to run idempotently here
        # even though the API process already created its own pool earlier
        # (StartupPlugin._startup_taskiq_broker — that pool stays live for
        # `add_schedule` from route handlers).
        scheduler_task = asyncio.create_task(
            run_scheduler_task(
                scheduler,
                run_startup=False,
                interval=timedelta(seconds=settings.TASKIQ_SCHEDULER_UPDATE_INTERVAL),
            ),
            name="taskiq_in_process_scheduler",
        )
        scheduler_task.add_done_callback(self._on_runtime_task_done)
        setattr(app.state, _SCHEDULER_TASK_ATTR, scheduler_task)
        logger.info(
            "TaskIQ in-process scheduler started (update_interval=%ds)",
            settings.TASKIQ_SCHEDULER_UPDATE_INTERVAL,
        )

    async def _stop_runtime(self, app: Litestar) -> None:
        from core.config.base import get_settings

        timeout = get_settings().taskiq.TASKIQ_WAIT_TASKS_TIMEOUT

        for attr in (_WORKER_TASK_ATTR, _SCHEDULER_TASK_ATTR):
            task: asyncio.Task | None = getattr(app.state, attr, None)
            if task is None or task.done():
                continue
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.warning(
                    "TaskIQ runtime task %s did not finish within %ds — "
                    "forcing shutdown",
                    attr,
                    timeout,
                )
            except Exception:  # noqa: BLE001
                logger.exception("TaskIQ runtime task %s failed during shutdown", attr)

        # Worker teardown: in shared-litestar mode this is intentionally a
        # no-op — `ShutdownPlugin` owns the engine + pgvector pool.
        from tasks.worker_lifecycle import teardown_worker_runtime

        await teardown_worker_runtime(share_with_litestar=True)

        # Flip the flag back so `ShutdownPlugin._shutdown_taskiq_broker`
        # fires CLIENT_SHUTDOWN instead of WORKER_SHUTDOWN. Otherwise the
        # standalone `_worker_shutdown_event` (registered for CLI use) would
        # call `teardown_worker_runtime(share_with_litestar=False)` here and
        # close the engine that `ShutdownPlugin._close_main_engine` is
        # about to close again — racing pgvector / sqlalchemy disposal.
        broker = getattr(app.state, "taskiq_broker", None)
        if broker is not None:
            broker.is_worker_process = False

    @staticmethod
    def _on_runtime_task_done(task: asyncio.Task) -> None:
        """Surface unexpected runtime task deaths in logs.

        `/health/live` separately checks `task.done()` and returns 503 when
        either runtime task has died, so Container Apps can recycle the
        replica even if the API itself is still answering.
        """
        if task.cancelled():
            logger.info("TaskIQ runtime task %s cancelled", task.get_name())
            return
        exc = task.exception()
        if exc is not None:
            logger.error(
                "TaskIQ runtime task %s exited with exception: %s",
                task.get_name(),
                exc,
                exc_info=exc,
            )
        else:
            logger.warning(
                "TaskIQ runtime task %s exited unexpectedly without an error",
                task.get_name(),
            )
