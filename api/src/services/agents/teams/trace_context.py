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


def current_or_new_trace_id() -> str:
    """Return the active OTel trace_id (hex), or a fresh URL-safe token.

    Pipeline entry points (webhook handler, admin preview run, manual
    `/process-file` command) used to call :func:`generate_trace_id` —
    producing a string disconnected from any OpenTelemetry span. Once
    the trace_id was persisted onto jobs / transcriptions / journal rows,
    operators had two parallel correlation ids: the DB string and the
    OTel span tree. They never joined.

    This helper closes the gap: when called inside a recording span
    (HTTP request, taskiq task body — both have a span open via
    `@observe` and the `TraceContextMiddleware`), the returned id is the
    OTel ``trace_id`` formatted as a 32-char lowercase hex string. Logs
    and DB rows then carry the same identifier Grafana shows on the
    span, so one click links them.

    When no span is active (worker spawned outside the broker middleware,
    test scaffolding, ad-hoc scripts) we fall back to the URL-safe token
    so the column never ends up null.
    """
    from opentelemetry import trace as otel_trace

    span_ctx = otel_trace.get_current_span().get_span_context()
    if span_ctx.is_valid and span_ctx.trace_id:
        return otel_trace.format_trace_id(span_ctx.trace_id)
    return generate_trace_id()


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
