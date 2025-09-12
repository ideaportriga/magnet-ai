from datetime import UTC, datetime


def utc_to_isoformat(utc_datetime: datetime) -> str:
    return utc_datetime.replace(tzinfo=UTC).isoformat()


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_isoformat() -> str:
    return utc_to_isoformat(utc_now())
