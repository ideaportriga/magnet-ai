"""Integration publish journal — idempotency + observability.

Wraps each external-system publish in stage 2 of the note-taker
pipeline. The journal table answers:

* "Did we already publish job X to Confluence on this run?" → skip.
* "Which integration failed for job Y?" → status + error + error_class.
* "How many retries before it succeeded?" → attempt_count.

Idempotency comes from ``UNIQUE(job_id, integration_kind)`` plus the
async context manager: it inserts a ``pending`` row, runs the publish,
then marks the row ``done`` / ``failed``. On a second run the unique
constraint detects the existing ``done`` row and the caller skips.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-4.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Any, AsyncIterator, Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.db.models.teams.note_taker_integration_attempt import (
    NoteTakerIntegrationAttempt,
)
from core.db.session import async_session_maker

logger = getLogger(__name__)

IntegrationKind = Literal["confluence", "salesforce", "knowledge_graph"]


# Outbox backoff schedule for failed integration publishes. The sweeper
# (`retry_failed_integrations_cron`) only picks up rows where
# `now() >= next_retry_at`. Attempts beyond `len(_RETRY_BACKOFF)` are
# considered terminally dead and excluded from the sweep by the
# `attempt_count < N` filter on the sweeper.
_RETRY_BACKOFF_SECONDS: tuple[int, ...] = (
    5 * 60,  # 1st retry: 5 min
    15 * 60,  # 2nd: 15 min
    60 * 60,  # 3rd: 1 h
    4 * 60 * 60,  # 4th: 4 h
)
RETRY_MAX_ATTEMPTS = len(_RETRY_BACKOFF_SECONDS) + 1  # initial attempt + 4 retries


def _next_retry_at(attempt_count: int) -> datetime | None:
    """Pick the next backoff slot, or None if the row is terminally dead."""
    idx = max(0, attempt_count - 1)
    if idx >= len(_RETRY_BACKOFF_SECONDS):
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=_RETRY_BACKOFF_SECONDS[idx])


async def is_already_done(*, job_id: str, integration_kind: IntegrationKind) -> bool:
    """Return True if this integration already finished successfully."""
    async with async_session_maker() as session:
        row = (
            await session.execute(
                select(NoteTakerIntegrationAttempt.status).where(
                    NoteTakerIntegrationAttempt.job_id == job_id,
                    NoteTakerIntegrationAttempt.integration_kind == integration_kind,
                )
            )
        ).scalar_one_or_none()
    return row == "done"


@contextlib.asynccontextmanager
async def integration_attempt(
    *,
    job_id: str,
    integration_kind: IntegrationKind,
    trace_id: str | None = None,
    skip_if_done: bool = True,
    retry_payload: dict[str, Any] | None = None,
) -> AsyncIterator[bool]:
    """Context manager that records one publish attempt.

    Yields ``True`` when the caller should proceed with the publish, and
    ``False`` when there's already a ``done`` row (idempotent skip). On
    exit, the row is marked ``done`` (no exception) or ``failed`` (with
    the exception class/message). The exception is re-raised so the
    caller still sees it.

    When ``retry_payload`` is provided it's persisted alongside the
    journal row; the outbox sweeper reads it to replay failed publishes
    without needing the original call context. Keep the payload minimal
    — kwargs for the relevant `*_bg_task.kiq(...)` invocation are enough.

    Usage::

        async with integration_attempt(
            job_id=jid,
            integration_kind="confluence",
            retry_payload={"job_id": jid, "settings_id": ...},
        ) as proceed:
            if proceed:
                await confluence.publish(...)
    """
    if not job_id:
        # No journal row possible without a job id — yield True for
        # backwards compatibility with admin-preview flows that bypass
        # job tracking. The publish still runs; we just lose retry
        # observability for it.
        yield True
        return

    if skip_if_done and await is_already_done(
        job_id=job_id, integration_kind=integration_kind
    ):
        logger.info(
            "integration_attempt: %s/%s already done — skipping",
            job_id,
            integration_kind,
        )
        yield False
        return

    # UPSERT a pending row, incrementing attempt_count on conflict
    # (so re-runs of failed integrations don't reset the counter).
    async with async_session_maker() as session:
        insert_values: dict[str, Any] = {
            "job_id": job_id,
            "integration_kind": integration_kind,
            "status": "pending",
            "attempt_count": 1,
            "trace_id": trace_id,
        }
        update_values: dict[str, Any] = {
            "status": "pending",
            "attempt_count": NoteTakerIntegrationAttempt.attempt_count + 1,
            "error": None,
            "error_class": None,
            "finished_at": None,
            "next_retry_at": None,
            "trace_id": trace_id,
        }
        if retry_payload is not None:
            insert_values["retry_payload"] = retry_payload
            update_values["retry_payload"] = retry_payload

        stmt = (
            pg_insert(NoteTakerIntegrationAttempt)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=["job_id", "integration_kind"],
                set_=update_values,
            )
        )
        await session.execute(stmt)
        await session.commit()

    # Pin the journal coordinates onto the currently-recording OTel span
    # so Grafana traces become searchable by `note_taker.job_id` and
    # `note_taker.integration_kind`. No-op when no span is active.
    try:
        from opentelemetry import trace as otel_trace

        _otel_span = otel_trace.get_current_span()
        if _otel_span.get_span_context().is_valid:
            _otel_span.set_attribute("note_taker.job_id", job_id)
            _otel_span.set_attribute("note_taker.integration_kind", integration_kind)
            if trace_id:
                _otel_span.set_attribute("note_taker.trace_id", trace_id)
    except Exception:  # noqa: BLE001
        logger.debug(
            "integration_attempt: OTel span attribute emit failed", exc_info=True
        )

    error: BaseException | None = None
    publish_started = asyncio.get_event_loop().time()
    try:
        yield True
    except BaseException as exc:  # noqa: BLE001 — record everything and re-raise
        error = exc
        raise
    finally:
        publish_seconds = asyncio.get_event_loop().time() - publish_started
        from sqlalchemy import update

        async with async_session_maker() as session:
            values: dict = {"finished_at": datetime.now(timezone.utc)}
            if error is None:
                values["status"] = "done"
                values["error"] = None
                values["error_class"] = None
                values["next_retry_at"] = None
            else:
                values["status"] = "failed"
                values["error"] = f"{error}"[:2000]
                values["error_class"] = type(error).__name__
                # Schedule the next retry slot. Read attempt_count from the
                # row we just UPSERT'd so the backoff matches reality even
                # after concurrent re-runs.
                attempt_row = (
                    await session.execute(
                        select(NoteTakerIntegrationAttempt.attempt_count).where(
                            NoteTakerIntegrationAttempt.job_id == job_id,
                            NoteTakerIntegrationAttempt.integration_kind
                            == integration_kind,
                        )
                    )
                ).scalar_one_or_none() or 1
                values["next_retry_at"] = _next_retry_at(attempt_row)
            await session.execute(
                update(NoteTakerIntegrationAttempt)
                .where(
                    NoteTakerIntegrationAttempt.job_id == job_id,
                    NoteTakerIntegrationAttempt.integration_kind == integration_kind,
                )
                .values(**values)
            )
            await session.commit()

        # Record latency for every publish attempt — outcome label tells
        # the dashboard whether to slice success vs failure.
        try:
            from .notetaker_metrics import (
                record_integration_failure,
                record_integration_publish_duration,
            )

            record_integration_publish_duration(
                integration=integration_kind,
                outcome="failed" if error is not None else "completed",
                seconds=publish_seconds,
            )
            # Emit failure counter only on failure so the dashboard alerts
            # are signal-only (success counts are derivable from the DB).
            if error is not None:
                record_integration_failure(
                    integration=integration_kind,
                    error_class=type(error).__name__,
                )
        except Exception:  # noqa: BLE001
            logger.debug("integration_journal: metric emit failed", exc_info=True)
