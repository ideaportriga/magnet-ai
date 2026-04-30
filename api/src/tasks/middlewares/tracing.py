"""Trace propagation: API process → worker process.

The API process enqueues a task while handling an HTTP request — it sits inside
an OpenTelemetry trace. The worker is a separate process, so the in-process OTel
context doesn't travel automatically. This middleware uses OTel's standard W3C
propagator to serialize the parent span (traceparent / tracestate) into message
labels on `pre_send`, and restores it on `pre_execute` by attaching a
`NonRecordingSpan` to the current context. That way any `@observe`-decorated
function inside the task becomes a child of the upstream trace — consistent
with the behaviour we had under APScheduler in a single process.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.propagate import extract, inject
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

logger = getLogger(__name__)

# Label keys carrying the W3C trace context inside the broker message.
# Must round-trip through JSON serialisation, so keep them flat strings.
_TRACEPARENT_LABEL = "traceparent"
_TRACESTATE_LABEL = "tracestate"

# Stash the detach-token on the message so post_execute can unwind the context.
_CTX_TOKEN_ATTR = "_mai_otel_ctx_token"


class TraceContextMiddleware(TaskiqMiddleware):
    """W3C trace-context propagation across the process boundary."""

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        try:
            carrier: dict[str, str] = {}
            inject(carrier)
            traceparent = carrier.get(_TRACEPARENT_LABEL)
            if traceparent:
                message.labels[_TRACEPARENT_LABEL] = traceparent
            tracestate = carrier.get(_TRACESTATE_LABEL)
            if tracestate:
                message.labels[_TRACESTATE_LABEL] = tracestate
        except Exception as exc:  # noqa: BLE001
            logger.debug("pre_send trace inject failed: %s", exc)
        return message

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        traceparent = message.labels.get(_TRACEPARENT_LABEL)
        if not traceparent:
            return message
        try:
            carrier = {_TRACEPARENT_LABEL: traceparent}
            tracestate = message.labels.get(_TRACESTATE_LABEL)
            if tracestate:
                carrier[_TRACESTATE_LABEL] = tracestate

            ctx = extract(carrier)
            # `extract` places the remote span into the returned context.
            # `attach` makes it the current OTel context so subsequent span
            # starts see it via `get_current_span()`.
            token = otel_context.attach(ctx)
            setattr(message, _CTX_TOKEN_ATTR, token)

            span = otel_trace.get_current_span(ctx)
            span_ctx = span.get_span_context() if span else None
            if span_ctx and span_ctx.is_valid:
                logger.debug(
                    "Restored remote trace for task %s: trace_id=%032x span_id=%016x",
                    message.task_name,
                    span_ctx.trace_id,
                    span_ctx.span_id,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("pre_execute trace extract failed: %s", exc)
        return message

    async def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        token = getattr(message, _CTX_TOKEN_ATTR, None)
        if token is None:
            return
        try:
            otel_context.detach(token)
        except Exception as exc:  # noqa: BLE001
            logger.debug("post_execute trace detach failed: %s", exc)
