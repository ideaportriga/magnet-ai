"""TaskiqScheduler with a single PG-backed source.

Runs as a separate `taskiq scheduler` process with `replicas: 1`. It does NOT
execute tasks — it only polls the source and enqueues due messages onto the
broker, which workers then consume.

We use `PreservingAsyncpgScheduleSource` (see `tasks/schedule_source.py`)
instead of the upstream `AsyncpgScheduleSource`: upstream truncates
`taskiq_schedules` on every startup and reinserts only static
`@broker.task(schedule=[...])` labels, which wipes every dynamic recurring
job added through `/admin/scheduler/create-job`. The variant upserts static
labels with deterministic ids and leaves dynamic rows alone.

We intentionally DO NOT add `LabelScheduleSource` alongside: the PG source
already owns the static labels, so adding an in-memory mirror would fire
each cron twice.
"""

from __future__ import annotations

import sys
from logging import getLogger

from taskiq import TaskiqScheduler

from tasks.broker import _POOL_KWARGS, _postgres_dsn, broker
from tasks.schedule_source import PreservingAsyncpgScheduleSource

# Import task modules so @broker.task registrations execute before
# AsyncpgScheduleSource.startup() extracts them via
# `extract_scheduled_tasks_from_broker()`. Must happen before `scheduler`
# is constructed.
import tasks.definitions  # noqa: F401
import tasks.schedules.system  # noqa: F401

logger = getLogger(__name__)


schedule_source = PreservingAsyncpgScheduleSource(
    dsn=_postgres_dsn(), broker=broker, **_POOL_KWARGS
)


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[schedule_source],
)


# `taskiq scheduler tasks.scheduler:scheduler` puts "scheduler" at argv[1].
# Other processes (API, `taskiq worker ...`) import this module too (to get
# `schedule_source` into `tasks.__init__`), so gate the log to avoid noise.
if len(sys.argv) > 1 and sys.argv[1] == "scheduler":
    logger.info(
        "TaskIQ scheduler process starting (sources=%d, broker=%s)",
        len(scheduler.sources),
        type(broker).__name__,
    )
