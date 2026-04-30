"""Worker startup/shutdown wiring — replaces `taskiq_litestar.init`.

The upstream `taskiq_litestar` integration enters/exits `app.lifespan()` via a
raw `__aenter__`/`__aexit__` pair. Litestar's lifespan uses
`anyio.create_task_group()` under the hood, whose cancel scope must be exited
from the same asyncio task it was entered on. TaskIQ invokes WORKER_STARTUP
and WORKER_SHUTDOWN on different tasks, so `__aexit__` raises
`RuntimeError: Attempted to exit cancel scope in a different task`. The
library logs it as a warning and moves on — but the task group is left
un-closed, background tasks inside it stay pending, and
`asyncio.run(listen(...))` can't finalise the loop on worker shutdown. The
worker process then hangs and has to be SIGKILL'd.

We work around it by running only the bits the tasks actually need (DB
engine, pgvector pool, storage registry) as plain async functions — no
`app.lifespan()`, no anyio TaskGroup, no cross-task cancel scopes.

The `setup_worker_runtime` / `teardown_worker_runtime` helpers are also
called from `TaskiqRuntimePlugin` in the in-process single-container layout:
there the API and the worker share the same Litestar app + DB engines, so
re-running the heavy init would just leak resources. The plugin invokes
them with `share_with_litestar=True` to make the helpers idempotent against
already-initialised state.
"""

from __future__ import annotations

from logging import getLogger

from taskiq import AsyncBroker, TaskiqEvents, TaskiqState

logger = getLogger(__name__)


async def setup_worker_runtime(
    state: TaskiqState | None = None,
    *,
    share_with_litestar: bool = False,
) -> None:
    """Initialise worker-side resources (DB, pgvector, storage).

    `share_with_litestar=True` is set when running in-process inside a
    Litestar app: DB engines and storage are already configured by
    `StartupPlugin`, so this becomes a near no-op (only LiteLLM callbacks
    + lazy settings warm-up still need to fire, and the broker's TaskiqState
    needs storage handles to satisfy `TaskiqDepends`).
    """
    from core.config.base import get_settings
    from core.server.plugins.startup import StartupPlugin

    plugin = StartupPlugin()
    plugin._register_litellm_callbacks()

    if not share_with_litestar:
        await plugin._initialize_database_connections()

    # Storage backends — used by sync_collection tasks via StorageService.
    # StartupPlugin._initialize_storage wants a Litestar app to stash state on;
    # tasks read storage lazily via module-level helpers, so we just run the
    # setup and discard the service instance.
    try:
        from storage import FileLimits, StorageConfig, StorageService, setup_storage
        from storage.lifecycle import register_storage_listeners

        cfg = StorageConfig()
        resolver = await setup_storage(cfg=cfg)
        if state is not None:
            state.storage_service = StorageService()
            state.file_limits = FileLimits(resolver=resolver, cfg=cfg)
            register_storage_listeners(state.storage_service)
        logger.info("Worker: storage module initialized")
    except Exception as exc:  # noqa: BLE001
        logger.error("Worker: failed to initialize storage module: %s", exc)

    # Materialise lazy-loaded settings so the first task doesn't pay the cost.
    get_settings()
    logger.info(
        "TaskIQ worker startup complete (shared_litestar=%s)", share_with_litestar
    )


async def teardown_worker_runtime(*, share_with_litestar: bool = False) -> None:
    """Release worker-side resources.

    With `share_with_litestar=True` we leave engine + pgvector pool alone:
    the Litestar `ShutdownPlugin` owns their lifecycle in the in-process
    layout and double-disposing breaks active sessions in flight.
    """
    if share_with_litestar:
        logger.info("TaskIQ worker teardown (shared_litestar): nothing to release")
        return

    try:
        from core.db.connection_manager import get_connection_manager

        await get_connection_manager().close_all()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Worker: failed to close DB engines cleanly: %s", exc)

    try:
        from stores.pgvector_db import pgvector_client

        await pgvector_client.close_pool()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Worker: pgvector pool already closed or not started: %s", exc)

    logger.info("TaskIQ worker shutdown complete")


# CLI-process event handlers (used by `taskiq worker` standalone). The
# in-process plugin does NOT rely on these — it calls the runtime helpers
# directly so it can pass `share_with_litestar=True`.
async def _worker_startup_event(state: TaskiqState) -> None:
    await setup_worker_runtime(state, share_with_litestar=False)


async def _worker_shutdown_event(state: TaskiqState) -> None:  # noqa: ARG001
    await teardown_worker_runtime(share_with_litestar=False)


def init(broker: AsyncBroker) -> None:
    """Register worker-only startup/shutdown hooks on the broker."""
    broker.add_event_handler(TaskiqEvents.WORKER_STARTUP, _worker_startup_event)
    broker.add_event_handler(TaskiqEvents.WORKER_SHUTDOWN, _worker_shutdown_event)
