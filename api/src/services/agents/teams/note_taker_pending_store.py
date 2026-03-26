"""
Persistence layer for speaker-mapping confirmation state (note_taker_pending_confirmation).

A pending record is created when transcription completes and the post_transcription
template produces a speaker mapping. The pipeline pauses and sends an Adaptive Card
to the user. When the user confirms (or skips), the record is loaded and deleted,
and post-processing continues.

Records expire after TTL_HOURS (default 24h). Expired records are ignored on load
and cleaned up lazily.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from stores import get_db_store

logger = logging.getLogger(__name__)

TABLE = "note_taker_pending_confirmation"
TTL_HOURS = 24


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
) -> str:
    """Persist a pending confirmation and return the record id (UUID str)."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TTL_HOURS)

    row = await get_db_store().client.fetchrow(
        f"""
        INSERT INTO {TABLE}
            (job_id, chat_id, bot_id, full_text,
             raw_speaker_mapping, suggested_keyterms,
             settings_system_name, settings_snapshot,
             meeting_context, invited_people, conversation_reference,
             pipeline_id, conversation_date, conversation_time,
             created_at, expires_at)
        VALUES
            ($1, $2, $3, $4,
             $5::jsonb, $6::jsonb,
             $7, $8::jsonb,
             $9::jsonb, $10::jsonb, $11::jsonb,
             $12, $13, $14,
             $15, $16)
        RETURNING id::text
        """,
        job_id,
        chat_id,
        bot_id,
        full_text,
        json.dumps(raw_speaker_mapping),
        json.dumps(suggested_keyterms),
        settings_system_name,
        json.dumps(settings_snapshot) if settings_snapshot is not None else None,
        json.dumps(meeting_context) if meeting_context is not None else None,
        json.dumps(invited_people) if invited_people is not None else None,
        json.dumps(conversation_reference)
        if conversation_reference is not None
        else None,
        pipeline_id,
        conversation_date,
        conversation_time,
        now,
        expires_at,
    )
    return str(row["id"])


async def load_pending(pending_id: str) -> dict[str, Any] | None:
    """
    Load a pending confirmation by id.
    Returns None if not found or already expired.
    Does NOT delete the record — call delete_pending() after processing.
    """
    row = await get_db_store().client.fetchrow(
        f"""
        SELECT id::text, job_id, chat_id, bot_id, full_text,
               raw_speaker_mapping, suggested_keyterms,
               settings_system_name, settings_snapshot,
               meeting_context, invited_people, conversation_reference,
               pipeline_id, conversation_date, conversation_time,
               created_at, expires_at
        FROM {TABLE}
        WHERE id = $1
        """,
        pending_id,
    )
    if not row:
        return None

    now = datetime.now(timezone.utc)
    expires_at = row["expires_at"]
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and now > expires_at:
        logger.info("Pending confirmation %s has expired, ignoring.", pending_id)
        await delete_pending(pending_id)
        return None

    def _json(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return v
        try:
            return json.loads(v)
        except Exception:
            return v

    return {
        "id": row["id"],
        "job_id": row["job_id"],
        "chat_id": row["chat_id"],
        "bot_id": row["bot_id"],
        "full_text": row["full_text"],
        "raw_speaker_mapping": _json(row["raw_speaker_mapping"]) or {},
        "suggested_keyterms": _json(row["suggested_keyterms"]) or [],
        "settings_system_name": row["settings_system_name"],
        "settings_snapshot": _json(row["settings_snapshot"]),
        "meeting_context": _json(row["meeting_context"]),
        "invited_people": _json(row["invited_people"]) or [],
        "conversation_reference": _json(row["conversation_reference"]),
        "pipeline_id": row["pipeline_id"],
        "conversation_date": row["conversation_date"],
        "conversation_time": row["conversation_time"],
    }


async def load_and_delete_pending(pending_id: str) -> dict[str, Any] | None:
    """
    Atomically load and delete a pending confirmation in a single query.
    Returns None if not found or already expired. Prevents double-processing
    because the DELETE ... RETURNING ensures only one caller gets the row.
    """
    row = await get_db_store().client.fetchrow(
        f"""
        DELETE FROM {TABLE}
        WHERE id = $1
        RETURNING id::text, job_id, chat_id, bot_id, full_text,
                  raw_speaker_mapping, suggested_keyterms,
                  settings_system_name, settings_snapshot,
                  meeting_context, invited_people, conversation_reference,
                  pipeline_id, conversation_date, conversation_time,
                  created_at, expires_at
        """,
        pending_id,
    )
    if not row:
        return None

    now = datetime.now(timezone.utc)
    expires_at = row["expires_at"]
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and now > expires_at:
        logger.info("Pending confirmation %s has expired, ignoring.", pending_id)
        return None

    def _json(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return v
        try:
            return json.loads(v)
        except Exception:
            return v

    return {
        "id": row["id"],
        "job_id": row["job_id"],
        "chat_id": row["chat_id"],
        "bot_id": row["bot_id"],
        "full_text": row["full_text"],
        "raw_speaker_mapping": _json(row["raw_speaker_mapping"]) or {},
        "suggested_keyterms": _json(row["suggested_keyterms"]) or [],
        "settings_system_name": row["settings_system_name"],
        "settings_snapshot": _json(row["settings_snapshot"]),
        "meeting_context": _json(row["meeting_context"]),
        "invited_people": _json(row["invited_people"]) or [],
        "conversation_reference": _json(row["conversation_reference"]),
        "pipeline_id": row["pipeline_id"],
        "conversation_date": row["conversation_date"],
        "conversation_time": row["conversation_time"],
    }


async def delete_pending(pending_id: str) -> None:
    """Delete a pending confirmation record (idempotent)."""
    await get_db_store().client.execute_command(
        f"DELETE FROM {TABLE} WHERE id = $1",
        pending_id,
    )


async def cleanup_expired() -> int:
    """Delete all expired pending confirmations. Returns number of rows deleted."""
    result = await get_db_store().client.execute_command(
        f"DELETE FROM {TABLE} WHERE expires_at < now()"
    )
    # asyncpg returns "DELETE N" string
    try:
        return int(str(result).split()[-1])
    except Exception:
        return 0
