"""Persistence layer for speaker-mapping confirmation state.

A pending record is created when transcription completes and the
post-transcription template produces a speaker mapping. The pipeline
pauses and sends an Adaptive Card to the user. When the user confirms
(or skips), the record is loaded-and-deleted in one query, and post-
processing continues.

Records expire after `TTL_HOURS`. Expired records are ignored on load
and swept by `tasks/schedules/system.py::cleanup_note_taker_pending_cron`.

Implementation now delegates to ``NoteTakerPendingConfirmationsService``
(advanced-alchemy) so JSONB columns ride the engine's serializer instead
of relying on the per-connection asyncpg type codec — the same JSONB-codec
race that motivated the recent transcriptions-domain migration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete

from core.db.models.teams.note_taker_pending_confirmation import (
    NoteTakerPendingConfirmation,
)
from core.db.session import async_session_maker
from core.domain.note_taker_pending_confirmations.service import (
    NoteTakerPendingConfirmationsService,
)

logger = logging.getLogger(__name__)

TABLE = "note_taker_pending_confirmation"
# Shortened from 24h after P1-1 (docs/NOTE_TAKER_RELIABILITY_PLAN.md):
# 24h was too long for a chat-flow confirmation — pending rows piled up
# instead of running, and stale conversation references inside them are
# more likely to fail when the user finally clicks the card. 6h covers
# the realistic window (post-meeting same-day review) while keeping the
# tail of forgotten rows much smaller.
TTL_HOURS = 6


def _row_to_dict(row: NoteTakerPendingConfirmation) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "job_id": row.job_id,
        "chat_id": row.chat_id,
        "bot_id": row.bot_id,
        "full_text": row.full_text,
        "raw_speaker_mapping": row.raw_speaker_mapping or {},
        "suggested_keyterms": row.suggested_keyterms or [],
        "settings_system_name": row.settings_system_name,
        "settings_snapshot": row.settings_snapshot,
        "meeting_context": row.meeting_context,
        "invited_people": row.invited_people or [],
        "conversation_reference": row.conversation_reference,
        "pipeline_id": row.pipeline_id,
        "conversation_date": row.conversation_date,
        "conversation_time": row.conversation_time,
        "trace_id": row.trace_id,
    }


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires_at


async def save_pending(
    *,
    job_id: str,
    chat_id: str | None,
    bot_id: str | None,
    full_text: str,
    raw_speaker_mapping: dict[str, str],
    suggested_keyterms: list[str],
    settings_system_name: str | None,
    settings_snapshot: dict[str, Any] | None,
    meeting_context: dict[str, Any] | None,
    invited_people: list[dict[str, str]] | None,
    conversation_reference: dict[str, Any] | None,
    pipeline_id: str | None,
    conversation_date: str | None,
    conversation_time: str | None,
    trace_id: str | None = None,
) -> str:
    """Persist a pending confirmation and return the record id (UUID str)."""
    from .trace_context import get_trace_id

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TTL_HOURS)

    row = NoteTakerPendingConfirmation(
        job_id=job_id,
        chat_id=chat_id,
        bot_id=bot_id,
        full_text=full_text,
        raw_speaker_mapping=raw_speaker_mapping,
        suggested_keyterms=suggested_keyterms,
        settings_system_name=settings_system_name,
        settings_snapshot=settings_snapshot,
        meeting_context=meeting_context,
        invited_people=invited_people,
        conversation_reference=conversation_reference,
        pipeline_id=pipeline_id,
        conversation_date=conversation_date,
        conversation_time=conversation_time,
        created_at=now,
        expires_at=expires_at,
        trace_id=trace_id or get_trace_id(),
    )
    async with async_session_maker() as session:
        service = NoteTakerPendingConfirmationsService(session=session)
        saved = await service.create(row, auto_commit=True)
    return str(saved.id)


async def load_pending(pending_id: str) -> dict[str, Any] | None:
    """Load a pending confirmation by id.

    Returns None if not found or already expired. Does NOT delete the
    record — call ``delete_pending`` after processing.
    """
    async with async_session_maker() as session:
        service = NoteTakerPendingConfirmationsService(session=session)
        row = await service.get_one_or_none(id=UUID(pending_id))
        if row is None:
            return None

        if _is_expired(row.expires_at):
            logger.info("Pending confirmation %s has expired, ignoring.", pending_id)
            await service.delete(row.id, auto_commit=True)
            return None

        return _row_to_dict(row)


async def load_and_delete_pending(pending_id: str) -> dict[str, Any] | None:
    """Atomically load and delete a pending confirmation.

    Prevents double-processing: only one caller observes the row because
    ``DELETE ... RETURNING`` retires it from the table in a single round-trip.
    Returns None if not found or expired.
    """
    async with async_session_maker() as session:
        result = await session.execute(
            delete(NoteTakerPendingConfirmation)
            .where(NoteTakerPendingConfirmation.id == UUID(pending_id))
            .returning(NoteTakerPendingConfirmation)
        )
        row = result.scalar_one_or_none()
        await session.commit()

    if row is None:
        return None
    if _is_expired(row.expires_at):
        logger.info("Pending confirmation %s has expired, ignoring.", pending_id)
        return None
    return _row_to_dict(row)


async def delete_pending(pending_id: str) -> None:
    """Delete a pending confirmation record (idempotent)."""
    async with async_session_maker() as session:
        service = NoteTakerPendingConfirmationsService(session=session)
        try:
            await service.delete(UUID(pending_id), auto_commit=True)
        except Exception:
            # Idempotent — missing row is fine.
            logger.debug("delete_pending: record %s not found.", pending_id)


async def cleanup_expired() -> int:
    """Delete all expired pending confirmations.

    Returns the number of rows deleted. Invoked from the hourly housekeeping
    cron in ``tasks/schedules/system.py``.
    """
    now = datetime.now(timezone.utc)
    async with async_session_maker() as session:
        result = await session.execute(
            delete(NoteTakerPendingConfirmation).where(
                NoteTakerPendingConfirmation.expires_at < now
            )
        )
        await session.commit()
    return int(result.rowcount or 0)
