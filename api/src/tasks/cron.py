"""Cron helpers: CronConfig → 5-field cron expression + next-run computation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytz
from croniter import croniter

from tasks.types import CronConfig


def _field(value: int | str | None, default: str = "*") -> str:
    """Convert a CronConfig field (APScheduler-style) to a cron expression token.

    APScheduler accepts `None` (= every value, i.e. "*") plus int or string
    specs like "*/5" or "1,3,5". We pass those through; `None` → "*".
    """
    if value is None:
        return default
    return str(value)


def cron_config_to_expression(cron: CronConfig) -> str:
    """Render a CronConfig as a 5-field cron expression: `m h dom mon dow`.

    Fields unused in 5-field cron (year, week, second, start_date, end_date)
    are dropped silently — AsyncpgScheduleSource doesn't support them anyway.
    """
    minute = _field(cron.minute, "0")
    hour = _field(cron.hour, "0")
    day_of_month = _field(cron.day)
    month = _field(cron.month)
    day_of_week = _field(cron.day_of_week)
    return f"{minute} {hour} {day_of_month} {month} {day_of_week}"


def compute_next_run(
    cron_expression: str, timezone: str = "UTC", base: datetime | None = None
) -> datetime:
    """Compute the next run time (UTC) for a cron expression in the given timezone."""
    tz = pytz.timezone(timezone)
    base_dt = base.astimezone(tz) if base else datetime.now(tz)
    itr = croniter(cron_expression, base_dt)
    return itr.get_next(datetime).astimezone(UTC)
