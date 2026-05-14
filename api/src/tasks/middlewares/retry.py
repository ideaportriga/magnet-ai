"""Per-task-type retry middleware.

Global retry is dangerous for user-initiated one-time tasks like `sync_collection`
or `evaluation` — a retry on timeout would run the side effect twice. This
middleware only retries a fixed allowlist of idempotent housekeeping tasks, and
never on timeout / cancellation.
"""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import Any

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

logger = getLogger(__name__)


IDEMPOTENT_TASK_NAMES: set[str] = {
    "recover_stuck_syncing_kg_sources",
    "recover_stuck_processing_jobs",
    "recover_stuck_transcription_jobs",
    "cleanup_logs",
    "cleanup_old_uploads",
    "cleanup_expired_refresh_tokens",
    "cleanup_note_taker_pending",
    "sync_knowledge_graph_source",
}

NEVER_RETRY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    asyncio.TimeoutError,
    asyncio.CancelledError,
)

MAX_RETRIES = 3
BASE_DELAY_S = 10
MAX_DELAY_S = 600


class PerTaskTypeRetryMiddleware(TaskiqMiddleware):
    """Retry only idempotent housekeeping tasks. Never on timeout."""

    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> None:
        if isinstance(exception, NEVER_RETRY_EXCEPTIONS):
            return

        if message.task_name not in IDEMPOTENT_TASK_NAMES:
            return

        retry_count = int(message.labels.get("retry_count", 0))
        if retry_count >= MAX_RETRIES:
            logger.warning(
                "Task %s exhausted %d retries", message.task_name, MAX_RETRIES
            )
            return

        delay = min(BASE_DELAY_S * (2**retry_count), MAX_DELAY_S)
        message.labels["retry_count"] = str(retry_count + 1)
        message.labels["delay"] = str(delay)
        logger.info(
            "Retrying task %s (attempt %d/%d) after %ds",
            message.task_name,
            retry_count + 1,
            MAX_RETRIES,
            delay,
        )
        await self.broker.kick(message)
