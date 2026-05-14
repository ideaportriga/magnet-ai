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

import contextlib
from datetime import datetime, timezone
from logging import getLogger
from typing import AsyncIterator, Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.db.models.teams.note_taker_integration_attempt import (
    NoteTakerIntegrationAttempt,
)
from core.db.session import async_session_maker

logger = getLogger(__name__)

IntegrationKind = Literal["confluence", "salesforce", "knowledge_graph"]


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
) -> AsyncIterator[bool]:
    """Context manager that records one publish attempt.

    Yields ``True`` when the caller should proceed with the publish, and
    ``False`` when there's already a ``done`` row (idempotent skip). On
    exit, the row is marked ``done`` (no exception) or ``failed`` (with
    the exception class/message). The exception is re-raised so the
    caller still sees it.

    Usage::

        async with integration_attempt(job_id=jid, integration_kind="confluence") as proceed:
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
        stmt = (
            pg_insert(NoteTakerIntegrationAttempt)
            .values(
                job_id=job_id,
                integration_kind=integration_kind,
                status="pending",
                attempt_count=1,
                trace_id=trace_id,
            )
            .on_conflict_do_update(
                index_elements=["job_id", "integration_kind"],
                set_={
                    "status": "pending",
                    "attempt_count": NoteTakerIntegrationAttempt.attempt_count + 1,
                    "error": None,
                    "error_class": None,
                    "finished_at": None,
                    "trace_id": trace_id,
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    error: BaseException | None = None
    try:
        yield True
    except BaseException as exc:  # noqa: BLE001 — record everything and re-raise
        error = exc
        raise
    finally:
        from sqlalchemy import update

        async with async_session_maker() as session:
            values: dict = {"finished_at": datetime.now(timezone.utc)}
            if error is None:
                values["status"] = "done"
                values["error"] = None
                values["error_class"] = None
            else:
                values["status"] = "failed"
                values["error"] = f"{error}"[:2000]
                values["error_class"] = type(error).__name__
            await session.execute(
                update(NoteTakerIntegrationAttempt)
                .where(
                    NoteTakerIntegrationAttempt.job_id == job_id,
                    NoteTakerIntegrationAttempt.integration_kind == integration_kind,
                )
                .values(**values)
            )
            await session.commit()

        # Emit a metric only on failure so the dashboard alerts are
        # signal-only (success counts are derivable from the DB).
        if error is not None:
            try:
                from .notetaker_metrics import record_integration_failure

                record_integration_failure(
                    integration=integration_kind,
                    error_class=type(error).__name__,
                )
            except Exception:  # noqa: BLE001
                logger.debug("integration_journal: metric emit failed", exc_info=True)
