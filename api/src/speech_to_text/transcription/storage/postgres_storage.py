from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, BinaryIO, Literal, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.db.models.transcription.transcription import Transcription
from core.db.session import async_session_maker
from utils.upload_handler import get_read_url_via_storage

from ..models import FileData

logger = logging.getLogger(__name__)


class PgDataStorage:
    """Persist transcription job state via the SQLAlchemy `Transcription` model.

    Public method signatures match the legacy adapter that the STT pipeline
    consumes (`save_audio`, `update_status`, `update_transcription`,
    `update_error`, `get_meta`, `get_transcription`, `get_audio_url`,
    `load_audio`, `delete_audio`, `insert_meta`, `_update_fields`).
    Implementation has been moved off raw asyncpg in `PgVectorClient` so the
    JSONB type-codec race that previously caused dict-decode failures in the
    admin preview path no longer applies — the engine's `json_serializer` /
    `json_deserializer` handles JSONB columns uniformly.
    """

    TABLE = "transcriptions"

    _ALLOWED_UPDATE_FIELDS = frozenset(
        {
            "status",
            "transcription",
            "error",
            "participants",
            "duration_seconds",
            "updated_at",
            "full_text",
        }
    )

    async def _insert_shell_if_missing(self, data: FileData) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            pg_insert(Transcription)
            .values(
                file_id=data.file_id,
                filename=data.file_name,
                file_ext=data.file_ext,
                content_type=data.content_type or "application/octet-stream",
                object_key=data.object_key,
                status="started",
                meeting_id=data.meeting_id,
                chat_id=data.chat_id,
                initiated_by=data.initiated_by,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(index_elements=[Transcription.file_id])
        )
        async with async_session_maker() as session:
            await session.execute(stmt)
            await session.commit()

    async def _update_fields(self, file_id: str, **fields: Any) -> None:
        if not fields:
            return

        invalid = set(fields) - self._ALLOWED_UPDATE_FIELDS
        if invalid:
            raise ValueError(f"Invalid update fields: {invalid}")

        fields["updated_at"] = datetime.now(timezone.utc)

        async with async_session_maker() as session:
            row = (
                await session.execute(
                    select(Transcription).where(Transcription.file_id == file_id)
                )
            ).scalar_one_or_none()
            if row is None:
                return
            for key, value in fields.items():
                setattr(row, key, value)
            await session.commit()

    async def _row_by_file_id(self, file_id: str) -> dict | None:
        async with async_session_maker() as session:
            row = (
                await session.execute(
                    select(Transcription).where(Transcription.file_id == file_id)
                )
            ).scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": str(row.id),
            "file_id": row.file_id,
            "filename": row.filename,
            "file_ext": row.file_ext,
            "object_key": row.object_key,
            "content_type": row.content_type,
            "status": row.status,
            "error": row.error,
            "participants": row.participants,
            "transcription": row.transcription,
            "full_text": row.full_text,
            "duration_seconds": row.duration_seconds,
            "meeting_id": row.meeting_id,
            "chat_id": row.chat_id,
            "initiated_by": row.initiated_by,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # Public API (signatures preserved for the STT pipeline)
    # ──────────────────────────────────────────────────────────────────────────────
    async def save_audio(self, data: FileData, stream: BinaryIO | None = None) -> str:
        try:
            await self._insert_shell_if_missing(data)
            await self._update_fields(data.file_id, status="in_progress")
            return data.file_id
        except Exception:
            logger.exception("STT: save_audio failed for %s", data.file_id)
            raise

    async def update_status(
        self,
        file_id: str,
        status: Literal[
            "started",
            "in_progress",
            "running",
            "transcribed",
            "diarized",
            "completed",
            "failed",
        ],
        job_id: Optional[str] = None,
        transcription: Optional[dict] = None,
        error: Optional[str] = None,
        participants: Optional[list[dict]] = None,
    ) -> None:
        try:
            patch: dict[str, Any] = {"status": status}
            if transcription is not None:
                patch["transcription"] = transcription
            if error is not None:
                patch["error"] = error
            if participants is not None:
                patch["participants"] = participants
            # `job_id` is part of the legacy signature but no column exists for
            # it — silently drop it to avoid breaking callers.
            await self._update_fields(file_id, **patch)
        except Exception:
            logger.exception("STT: update_status failed for %s", file_id)
            raise

    async def update_transcription(self, file_id: str, transcription: dict) -> None:
        logger.info(
            "STT: update_transcription for %s (len=%s)",
            file_id,
            len(str(transcription)),
        )
        await self.update_status(file_id, "completed", transcription=transcription)

    async def update_error(self, file_id: str, message: str) -> None:
        logger.info("STT: update_error for %s: %s", file_id, message)
        await self.update_status(file_id, "failed", error=message)

    async def get_file(self, file_id: str) -> BinaryIO:
        raise NotImplementedError(
            "Raw audio is not stored in DB. Fetch from object storage instead."
        )

    async def get_transcription(self, file_id: str) -> Optional[dict]:
        try:
            row = await self._row_by_file_id(file_id)
            return (row or {}).get("transcription")
        except Exception:
            logger.exception("STT: get_transcription failed for %s", file_id)
            raise

    async def get_meta(self, file_id: str) -> dict | None:
        try:
            row = await self._row_by_file_id(file_id)
            if not row:
                return None
            created_at = row.get("created_at")
            updated_at = row.get("updated_at")
            return {
                "file_id": row.get("file_id"),
                "filename": row.get("filename"),
                "file_ext": row.get("file_ext"),
                "content_type": row.get("content_type"),
                "status": row.get("status"),
                "job_id": None,
                "duration": row.get("duration_seconds"),
                "error": row.get("error"),
                "participants": row.get("participants"),
                "transcription": row.get("transcription"),
                "meeting_id": row.get("meeting_id"),
                "chat_id": row.get("chat_id"),
                "initiated_by": row.get("initiated_by"),
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        except Exception:
            logger.exception("STT: get_meta failed for %s", file_id)
            raise

    async def delete_audio(self, file_id: str) -> None:
        logger.info("STT: delete_audio noop (not storing raw bytes) for %s", file_id)

    async def insert_meta(self, data: FileData) -> None:
        await self._insert_shell_if_missing(data)

    async def load_audio(self, file_id: str) -> bytes:
        from stores import get_db_store

        row = await self._row_by_file_id(file_id)
        object_key = row.get("object_key") if row else None

        if object_key:
            return await get_db_store().objects.get_bytes(object_key)

        raise RuntimeError("Audio bytes unavailable.")

    async def get_audio_url(self, file_id: str) -> str:
        async with async_session_maker() as session:
            object_key = (
                await session.execute(
                    select(Transcription.object_key).where(
                        Transcription.file_id == file_id
                    )
                )
            ).scalar_one_or_none()
        if not object_key:
            raise RuntimeError(f"Database has no object_key for file {file_id}")
        return await get_read_url_via_storage(object_key)
