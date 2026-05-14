"""Cross-stage correlation id for the note-taker pipeline.

The flow that records a meeting and publishes notes spans:

  Graph webhook → taskiq worker → STT submit + polling → stage 1 LLM →
  pending confirmation → user action → stage 2 LLM → Confluence/SF/KG

These steps live in different processes, run minutes (sometimes hours)
apart, and write to different tables. Without a shared id, joining logs
in Loki means hand-correlation through job_id, subscription_id, chat_id.

This module provides:

* :func:`generate_trace_id` — short, URL-safe correlation id.
* :data:`current_trace_id` — :class:`contextvars.ContextVar` set at each
  entry point so any log emitted within that context gets the id for
  free.
* :class:`TraceIdLogFilter` — :class:`logging.Filter` that injects the
  current trace id onto every :class:`logging.LogRecord` (as
  ``record.trace_id``). Wire it up once in the logging config and every
  formatter or Loki shipper can include it.
* :func:`set_trace_id` / :func:`bind_trace_id` — explicit setters for
  worker entry points.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.
"""

from __future__ import annotations

import contextlib
import logging
import secrets
from contextvars import ContextVar, Token
from typing import Iterator

current_trace_id: ContextVar[str | None] = ContextVar(
    "note_taker_trace_id", default=None
)


def generate_trace_id() -> str:
    """Return a fresh, short, URL-safe correlation id (≈22 chars)."""
    return secrets.token_urlsafe(16)


def set_trace_id(trace_id: str | None) -> Token:
    """Bind ``trace_id`` to the current async context.

    Returns the :class:`Token` from :meth:`ContextVar.set` so the caller
    can :meth:`reset` it later — prefer :func:`bind_trace_id` as a
    context manager for that.
    """
    return current_trace_id.set(trace_id)


@contextlib.contextmanager
def bind_trace_id(trace_id: str | None) -> Iterator[str | None]:
    """Context manager: bind ``trace_id`` for the body, restore on exit."""
    token = current_trace_id.set(trace_id)
    try:
        yield trace_id
    finally:
        current_trace_id.reset(token)


def get_trace_id() -> str | None:
    """Return the trace id bound to the current context, or ``None``."""
    return current_trace_id.get()


class TraceIdLogFilter(logging.Filter):
    """Inject ``record.trace_id`` from the contextvar onto every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "trace_id", None):
            record.trace_id = current_trace_id.get()
        return True


def add_trace_id_to_event_dict(_logger, _method_name, event_dict):
    """structlog processor: inject the contextvar's trace_id.

    Wire it into the project's structlog processor chains (see
    ``core/config/app.py``) so every emitted log line carries the
    correlation id as a top-level field, ready for ``| json | trace_id=...``
    queries in Loki.
    """
    if event_dict.get("trace_id"):
        return event_dict
    tid = current_trace_id.get()
    if tid:
        event_dict["trace_id"] = tid
    return event_dict
