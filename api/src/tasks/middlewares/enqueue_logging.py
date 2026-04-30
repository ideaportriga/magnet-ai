"""Logs a concise line every time a task is sent to the broker.

Fires on `pre_send`, which covers both paths:
- API-initiated `task.kiq(...)` from route handlers;
- Scheduler-process kicks of cron / scheduled-time tasks.

Keeps the payload small: task name, task_id, job_id (if any), and a trimmed
kwargs preview so we don't dump large arguments to Loki.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from taskiq import TaskiqMessage, TaskiqMiddleware

logger = getLogger(__name__)

_KWARGS_PREVIEW_LIMIT = 200


def _preview(value: Any) -> str:
    text = repr(value)
    if len(text) <= _KWARGS_PREVIEW_LIMIT:
        return text
    return text[:_KWARGS_PREVIEW_LIMIT] + "…"


class EnqueueLoggingMiddleware(TaskiqMiddleware):
    """Emit a one-line log for every broker enqueue."""

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        job_id = (
            message.kwargs.get("job_id") if isinstance(message.kwargs, dict) else None
        )
        schedule_id = message.labels.get("schedule_id") if message.labels else None
        logger.info(
            "Enqueued task %s (task_id=%s, job_id=%s, schedule_id=%s, kwargs=%s)",
            message.task_name,
            message.task_id,
            job_id,
            schedule_id,
            _preview(message.kwargs),
        )
        return message
