"""Task-lifecycle middleware: per-task DB session + singleton reset.

The TaskIQ worker is a long-lived process that executes many tasks in sequence.
Domain code (data_sync, storage, pgvector) was written for HTTP-request-scoped
sessions — it relies on Litestar's `before_send_handler="autocommit"` hook
firing at the end of a request to commit/release sessions. That hook never
fires in worker context, so any domain-code path that forgets to explicitly
commit/rollback leaks its session — connections stay checked out from the
pool until garbage collection or the PG idle_in_transaction timeout.

Under APScheduler (in-process), leaks were tolerated because real HTTP traffic
kept flushing the pool. Under TaskIQ (separate long-lived process), they
accumulate and hang the next task.

This middleware makes each task a hermetic unit regardless of domain-code
hygiene:

- Before task: open a fresh AsyncSession, attach it to shared domain singletons
  (`store.storage_db_session` used by the data-sync pipeline).
- After task: explicitly commit (on success) or rollback (on failure), then
  close and detach. Next task starts with clean state.

Combined with the worker CLI flag `--max-tasks-per-child 20`, this gives two
layers of defense: (1) middleware cleanly releases per-task state, (2) after
N tasks the child process respawns and any state we missed is forcibly
released (OS closes its sockets).
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

logger = getLogger(__name__)

_DOMAIN_SESSION_ATTRS = ("storage_db_session",)


class PerTaskLifecycleMiddleware(TaskiqMiddleware):
    """Open a fresh DB session per task, attach to domain singletons, release after.

    The session is attached to the `tasks.session` ContextVar and to known
    domain-singleton attributes. Task code that opens its own sessions via
    `alchemy.get_session()` still works — they live alongside the
    middleware-managed session.
    """

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        # Reset any stale session attributes on domain singletons. Should have
        # been cleaned by the previous post_execute, but be defensive: a crash
        # in a prior task could have left them dangling.
        self._reset_domain_singletons()

        try:
            from core.config.app import alchemy

            session_cm = alchemy.get_session()
            session = await session_cm.__aenter__()
            # Store the context manager + session on the message so post_execute
            # can release them. `message.labels` is the only obvious place to
            # carry non-serialisable state between the two middleware hooks
            # on the same message.
            setattr(message, "_mai_session_cm", session_cm)
            setattr(message, "_mai_session", session)
            self._attach_session_to_singletons(session)
        except Exception as exc:  # noqa: BLE001
            logger.warning("pre_execute: failed to open task session: %s", exc)

        return message

    async def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        session = getattr(message, "_mai_session", None)
        session_cm = getattr(message, "_mai_session_cm", None)

        if session is not None:
            try:
                if result.is_err:
                    await session.rollback()
                else:
                    await session.commit()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "post_execute: commit/rollback failed for task %s: %s",
                    message.task_name,
                    exc,
                )
                try:
                    await session.rollback()
                except Exception:  # noqa: BLE001
                    pass

        if session_cm is not None:
            try:
                await session_cm.__aexit__(None, None, None)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "post_execute: session close failed for task %s: %s",
                    message.task_name,
                    exc,
                )

        # Always detach from singletons, even if we never opened a session
        # (pre_execute may have failed).
        self._reset_domain_singletons()

    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> None:
        # on_error fires BEFORE post_execute. Log the full traceback so
        # failures are never silent.
        logger.error(
            "Task %s (id=%s) raised %s: %s",
            message.task_name,
            message.task_id,
            type(exception).__name__,
            exception,
            exc_info=exception,
        )

    @staticmethod
    def _attach_session_to_singletons(session: Any) -> None:
        """Wire the per-task session into module-level domain singletons.

        data_sync's file_data_processor reads `store.storage_db_session` for
        `StorageService.get(...)` calls. Without this, the store either has no
        session (first run) or a stale one from a previous task.
        """
        try:
            from stores import get_db_store

            store = get_db_store()
            store.storage_db_session = session
            # StorageService is idempotent, keep the existing instance if any
            if getattr(store, "storage_service", None) is None:
                from storage import StorageService

                store.storage_service = StorageService()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not attach session to store: %s", exc)

    @staticmethod
    def _reset_domain_singletons() -> None:
        """Clear per-task attributes from module-level singletons."""
        try:
            from stores import get_db_store

            store = get_db_store()
            for attr in _DOMAIN_SESSION_ATTRS:
                if hasattr(store, attr):
                    setattr(store, attr, None)
        except Exception:  # noqa: BLE001
            pass
