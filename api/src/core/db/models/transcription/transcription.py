# transcriptions.py

from __future__ import annotations
from typing import Optional
from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from advanced_alchemy.mixins import AuditColumns
from advanced_alchemy.types import JsonB
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text


class Transcription(
    CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs, AuditColumns
):
    __tablename__ = "transcriptions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True,
    )

    # Tenant boundary. Populated by `_insert_shell_if_missing` from the
    # `current_tenant_id` contextvar (set by auth middleware on HTTP
    # entry, by `rls_context_scope` on the taskiq side). Migration
    # j4k5l6m7n8o9 keeps the column NULLABLE during the transition
    # window — RLS still excludes NULL rows because the policy compares
    # against `NULLIF(current_setting('app.tenant_id'), '')::uuid` and
    # `NULL = ...` is `NULL` (not `true`). A follow-up migration will
    # flip NOT NULL once telemetry shows zero NULL inserts. See
    # NOTE_TAKER_REVISION_PLAN.md §3.4 P3-b.
    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    file_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="External file/job id used by API",
    )

    filename: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    file_ext: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    object_key: Mapped[Optional[str]] = mapped_column(Text(), nullable=True, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'started'"),
        index=True,
    )

    error: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    participants: Mapped[Optional[dict]] = mapped_column(JsonB, nullable=True)
    transcription: Mapped[Optional[dict]] = mapped_column(JsonB, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    meeting_id: Mapped[Optional[str]] = mapped_column(Text(), nullable=True, index=True)
    chat_id: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    initiated_by: Mapped[Optional[str]] = mapped_column(
        Text(), nullable=True, index=True
    )

    # Correlation id flowing from the webhook / preview entry-point so
    # logs from STT poll loops can be joined against the upstream caller.
    # See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.
    trace_id: Mapped[Optional[str]] = mapped_column(Text(), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<Transcription file_id={self.file_id} status={self.status}>"
