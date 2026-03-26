"""NoteTakerJob — preview pipeline job tracking."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class NoteTakerJob(UUIDv7AuditBase):
    """A preview pipeline job launched from the admin panel."""

    __tablename__ = "note_taker_jobs"

    settings_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("note_taker_settings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to the note_taker_settings record this job belongs to.",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, index=True, comment="User who triggered the job."
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
