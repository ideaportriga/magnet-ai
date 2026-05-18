"""NoteTakerJob — preview pipeline job tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User


class NoteTakerJob(UUIDv7AuditBase):
    """A preview pipeline job launched from the admin panel.

    Tenant + record-level access fields mirror the rest of the PR 10 rollout
    cohort (see migration h2i3j4k5l6m7). `owner_id` is set from the auth
    context on create; legacy `user_id` (Text) is preserved for backward
    compatibility with the existing Teams-side ownership check.
    """

    __tablename__ = "note_taker_jobs"
    __table_args__ = (
        Index("ix_note_taker_jobs_tenant_id", "tenant_id"),
        Index("ix_note_taker_jobs_owner_id", "owner_id"),
        Index("ix_note_taker_jobs_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_note_taker_jobs_visibility",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="private",
        server_default="private",
    )

    tenant: Mapped["Tenant"] = relationship(lazy="noload")
    owner: Mapped[Optional["User"]] = relationship(lazy="noload")
    department: Mapped[Optional["Department"]] = relationship(lazy="noload")

    settings_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("note_taker_settings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to the note_taker_settings record this job belongs to.",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        index=True,
        comment=(
            "Legacy string identifier of the principal who triggered the job. "
            "Kept for backward compatibility — new code should use `owner_id`."
        ),
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="URL or filename of the source media."
    )
    participants: Mapped[Optional[list[str]]] = mapped_column(
        JsonB, nullable=True, comment="Participant names for speaker mapping hints."
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="Job status: pending | running | completed | failed | rerunning.",
    )
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Job output (transcription, postprocessing, errors).",
    )

    # Correlation id propagated from the originating webhook / preview
    # request through STT and post-processing. See
    # docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.
    trace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
