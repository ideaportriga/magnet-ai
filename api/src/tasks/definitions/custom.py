"""CUSTOM run configuration — user-defined arbitrary job (placeholder executor).

Historically a stub that only logs parameters. Kept for API compatibility.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from services.observability import observability_context, observe
from tasks.broker import broker
from tasks.status import with_job_status

logger = getLogger(__name__)


@broker.task(task_name="custom_function")
@with_job_status
@observe(name="Custom job", channel="Job")
async def custom_function_task(*, job_id: str | None = None, **params: Any) -> bool:
    observability_context.update_current_trace(
        extra_data={"job_id": job_id, "params": params or {}},
    )
    logger.info("custom_function job %s params=%s", job_id, params)
    return True
