"""In-memory error collector for e2e testing.

Captures ERROR/CRITICAL level structlog events during test runs.
Only active when DEBUG_MODE=True. Never use in production.
"""

from __future__ import annotations

import sys
import threading
import traceback
from typing import Any


class TestErrorCollector:
    def __init__(self) -> None:
        self._errors: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def add_error(self, entry: dict[str, Any]) -> None:
        with self._lock:
            self._errors.append(entry)

    def get_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._errors)

    def reset(self) -> None:
        with self._lock:
            self._errors.clear()


_collector = TestErrorCollector()


def error_collector_processor(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that captures error/critical logs into the test collector."""
    level = event_dict.get("level", method)
    if level in ("error", "critical"):
        entry: dict[str, Any] = {
            "level": level,
            "event": event_dict.get("event", event_dict.get("message", "")),
            "timestamp": event_dict.get("timestamp", ""),
            "filename": event_dict.get("filename", ""),
            "func_name": event_dict.get("func_name", ""),
            "lineno": event_dict.get("lineno", ""),
        }

        exc_info = event_dict.get("exc_info")
        if exc_info is True:
            exc = sys.exc_info()
            if exc[0] is not None:
                entry["traceback"] = "".join(traceback.format_exception(*exc))
        elif isinstance(exc_info, BaseException):
            entry["traceback"] = "".join(
                traceback.format_exception(
                    type(exc_info), exc_info, exc_info.__traceback__
                )
            )
        elif (
            isinstance(exc_info, tuple)
            and len(exc_info) == 3
            and exc_info[0] is not None
        ):
            entry["traceback"] = "".join(traceback.format_exception(*exc_info))

        _collector.add_error(entry)

    return event_dict


def get_collector() -> TestErrorCollector:
    return _collector
