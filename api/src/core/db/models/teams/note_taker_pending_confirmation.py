"""NoteTakerPendingConfirmation — speaker-mapping confirmation pending user reply.

Holds a paused pipeline state: post-transcription has produced a speaker
mapping suggestion, an Adaptive Card was shown to the user in Teams, and
the pipeline is waiting for the user to confirm or skip. The record is
loaded-and-deleted in one query when the user replies (preventing
double-processing); expired rows are swept by `cleanup_note_taker_pending_cron`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from advanced_alchemy.types import JsonB
from sqlalchemy import DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column


class NoteTakerPendingConfirmation(
    CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs
):
    __tablename__ = "note_taker_pending_confirmation"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    job_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    chat_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    bot_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    raw_speaker_mapping: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True
    )
    suggested_keyterms: Mapped[Optional[list[str]]] = mapped_column(
        JsonB, nullable=True
    )

    settings_system_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    settings_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True
    )

    meeting_context: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True
    )
    invited_people: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True
    )
    conversation_reference: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True
    )

    pipeline_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_time: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    # Correlation id, propagated into stage 2 so log searches across both
    # stages line up. See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.
    trace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
