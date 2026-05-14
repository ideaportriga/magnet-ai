"""NoteTakerIntegrationAttempt — journal of side-effect publishes.

Stage 2 of the note-taker pipeline pushes a finished recording into
multiple external systems (Confluence, Salesforce, Knowledge Graph). If
one of them fails the other publishes should still complete, and a
second user-triggered run of the same job must not duplicate work that
already succeeded.

This table stores one row per (job_id, integration_kind):

* ``UNIQUE(job_id, integration_kind)`` — re-runs of stage 2 skip
  integrations already marked ``done``.
* ``status`` — ``pending`` while the call is in flight, then ``done``
  or ``failed`` — gives dashboards an at-a-glance view of which
  integration silently dropped a meeting.
* ``error`` / ``error_class`` — useful for ad-hoc bucketing in Loki and
  for the retry layer (P1-4 phase 2) to decide which failures are
  transient.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-4.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from sqlalchemy import DateTime, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column


class NoteTakerIntegrationAttempt(
    CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs
):
    """One row per (job_id, integration_kind) — see module docstring."""

    __tablename__ = "note_taker_integration_attempt"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "integration_kind",
            name="uq_note_taker_integration_attempt_job_kind",
        ),
        Index("ix_note_taker_integration_attempt_status", "status"),
        Index("ix_note_taker_integration_attempt_job_id", "job_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    job_id: Mapped[str] = mapped_column(Text, nullable=False)
    integration_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="confluence | salesforce | knowledge_graph",
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
        comment="pending | done | failed",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    error_class: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
