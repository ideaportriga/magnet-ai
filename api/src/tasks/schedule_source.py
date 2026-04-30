"""Persistence-preserving variant of `AsyncpgScheduleSource`.

The upstream source truncates `taskiq_schedules` on every scheduler startup
and reinserts only static `@broker.task(schedule=[...])` labels, assigning a
fresh `uuid4()` per call. Any recurring / scheduled-time jobs created via
`task.schedule_by_cron(...)` / `schedule_by_time(...)` are wiped — so jobs
added through `/admin/scheduler/create-job` silently stop firing after the
next scheduler restart.

Here:
- We do not truncate on startup.
- Static labels get a deterministic `schedule_id` (UUID5 over task name +
  schedule payload), so `INSERT ... ON CONFLICT DO UPDATE` is idempotent
  across restarts. Static rows are tagged with a `_static: "1"` label so
  stale statics (decorator removed from code) can be cleaned out on the
  next start without touching dynamic user schedules.
- Dynamic schedules (no `_static` label) are never touched by startup.
"""

from __future__ import annotations

import json
import uuid
from logging import getLogger
from typing import Any

import asyncpg
from pydantic import ValidationError
from taskiq import ScheduledTask
from taskiq_pg.asyncpg import AsyncpgScheduleSource
from taskiq_pg.asyncpg.queries import (
    CREATE_SCHEDULES_TABLE_QUERY,
    INSERT_SCHEDULE_QUERY,
)

logger = getLogger(__name__)

# Stable namespace UUID for hashing static schedule_ids. Do not change —
# rotating it reshuffles every existing static row and leaves orphans.
_STATIC_NS = uuid.UUID("49a1e8d6-6e62-4a8d-ba4e-7e0a1b84b7e2")

_STATIC_LABEL = "_static"

_DELETE_STATIC_NOT_IN_QUERY = (
    "DELETE FROM {} "
    "WHERE schedule->'labels'->>'{}' = '1' "
    "AND NOT (id = ANY($1::uuid[]))"
)
_DELETE_ALL_STATIC_QUERY = "DELETE FROM {} WHERE schedule->'labels'->>'{}' = '1'"
# One-time migration away from the upstream `AsyncpgScheduleSource.startup()`,
# which inserted static-label rows with a fresh `uuid4` on every restart and
# never added a marker we can recognise. Any row whose `task_name` matches a
# task that currently carries a `schedule=[...]` decorator but lacks the
# `_static` label is an old upstream-inserted static — remove it so we don't
# end up with both the legacy row (uuid4) and the new deterministic row
# (uuid5) firing the same cron twice.
_DELETE_UNFLAGGED_STATICS_QUERY = (
    "DELETE FROM {} "
    "WHERE task_name = ANY($1::text[]) "
    "AND (schedule->'labels'->>'{}') IS DISTINCT FROM '1'"
)


class PreservingAsyncpgScheduleSource(AsyncpgScheduleSource):
    """AsyncpgScheduleSource that keeps dynamic schedules across restarts."""

    async def startup(self) -> None:
        self._database_pool = await asyncpg.create_pool(
            dsn=self.dsn, **self._connect_kwargs
        )
        await self._database_pool.execute(
            CREATE_SCHEDULES_TABLE_QUERY.format(self._table_name)
        )

        static_schedules = self._extract_static_schedules_stable()
        static_ids = [uuid.UUID(s.schedule_id) for s in static_schedules]

        static_task_names = sorted({s.task_name for s in static_schedules})

        async with self._database_pool.acquire() as conn, conn.transaction():
            # Purge legacy unflagged statics from previous upstream runs.
            if static_task_names:
                await conn.execute(
                    _DELETE_UNFLAGGED_STATICS_QUERY.format(
                        self._table_name, _STATIC_LABEL
                    ),
                    static_task_names,
                )

            # Evict flagged statics whose decorator has been removed.
            if static_ids:
                await conn.execute(
                    _DELETE_STATIC_NOT_IN_QUERY.format(self._table_name, _STATIC_LABEL),
                    static_ids,
                )
            else:
                await conn.execute(
                    _DELETE_ALL_STATIC_QUERY.format(self._table_name, _STATIC_LABEL)
                )

            for schedule in static_schedules:
                await conn.execute(
                    INSERT_SCHEDULE_QUERY.format(self._table_name),
                    str(schedule.schedule_id),
                    schedule.task_name,
                    schedule.model_dump_json(exclude={"schedule_id", "task_name"}),
                )

        logger.info(
            "Schedule source ready: %d static schedule(s) upserted, "
            "dynamic schedules preserved",
            len(static_schedules),
        )

    def _extract_static_schedules_stable(self) -> list[ScheduledTask]:
        """Like upstream `extract_scheduled_tasks_from_broker`, but with
        deterministic `schedule_id` and a `_static` marker in labels so
        startup can upsert idempotently and evict removed decorators.
        """
        result: list[ScheduledTask] = []
        for task_name, task in self._broker.get_all_tasks().items():
            raw_schedule = task.labels.get("schedule")
            if not isinstance(raw_schedule, list):
                continue
            for schedule in raw_schedule:
                payload: dict[str, Any] = {
                    "labels": {
                        **schedule.get("labels", {}),
                        _STATIC_LABEL: "1",
                    },
                    "args": schedule.get("args", []),
                    "kwargs": schedule.get("kwargs", {}),
                    "cron": schedule.get("cron"),
                    "cron_offset": schedule.get("cron_offset"),
                    "interval": schedule.get("interval"),
                    "time": schedule.get("time"),
                }
                stable_id = str(
                    uuid.uuid5(
                        _STATIC_NS,
                        task_name + json.dumps(payload, sort_keys=True, default=str),
                    )
                )
                try:
                    result.append(
                        ScheduledTask.model_validate(
                            {
                                "task_name": task_name,
                                "schedule_id": stable_id,
                                **payload,
                            }
                        )
                    )
                except ValidationError:
                    logger.exception(
                        "Static schedule for task %s failed validation; skipped",
                        task_name,
                    )
                    continue
        return result
