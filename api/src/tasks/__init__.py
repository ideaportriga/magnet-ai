"""TaskIQ-based task queue and scheduler for magnet-ai.

Replaces the legacy APScheduler implementation. See docs/TASKIQ_MIGRATION_PLAN.md.

- `broker` — AsyncpgBroker + AsyncpgResultBackend (PostgreSQL LISTEN/NOTIFY).
- `scheduler` — TaskiqScheduler with LabelScheduleSource (static) and
  AsyncpgScheduleSource (dynamic per-user cron / scheduled tasks).
- `definitions/` — task implementations grouped by domain.
- `schedules/system.py` — builtin cron tasks registered at module import.
"""

from tasks.broker import broker
from tasks.scheduler import scheduler, schedule_source

__all__ = ["broker", "scheduler", "schedule_source"]
