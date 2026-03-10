from datetime import UTC, datetime


def utc_to_isoformat(utc_datetime: datetime) -> str:
    return utc_datetime.replace(tzinfo=UTC).isoformat()


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_isoformat() -> str:
    return utc_to_isoformat(utc_now())


def parse_date_string(date_str: str | None) -> datetime | None:
    """Parse a date string in YYYY-MM-DD format (e.g. '2025-05-16') to naive datetime at midnight."""

    if not date_str:
        return None

    return datetime.strptime(date_str, "%Y-%m-%d")
