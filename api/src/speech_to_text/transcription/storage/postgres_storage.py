from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import BinaryIO, Optional, Literal
from datetime import timezone
import time
from typing import Tuple
from ..models import FileData
from utils.upload_handler import get_read_url

from stores import get_db_store

logger = logging.getLogger(__name__)
store = get_db_store() 
# _BYTES_CACHE: dict[str, Tuple[float, bytes]] = {}
# _CACHE_TTL_SECONDS = 15 * 60  # 15 minutes; adjust as needed

# def _cache_put(file_id: str, b: bytes) -> None:
#     if not b:
#         return
#     _BYTES_CACHE[file_id] = (time.time() + _CACHE_TTL_SECONDS, b)

# def _cache_get(file_id: str) -> Optional[bytes]:
#     item = _BYTES_CACHE.get(file_id)
#     if not item:
#         return None
#     exp, b = item
#     if time.time() > exp:
#         _BYTES_CACHE.pop(file_id, None)
#         return None
#     return b

class PgDataStorage:
    """Store transcription job state in plain SQL table `transcriptions` (no embeddings)."""

    TABLE = "transcriptions"

    async def _insert_shell_if_missing(self, data: FileData) -> None:
        now = datetime.now(timezone.utc)
        await store.client.execute_command(
            """
            INSERT INTO transcriptions
                (file_id, filename, file_ext, content_type, object_key, status, created_at, updated_at)
            VALUES
                ($1,      $2,       $3,       $4,           $5,         'started', $6,         $7)
            ON CONFLICT (file_id) DO NOTHING
            """,
            data.file_id,
            data.file_name,                                  # or data.filename_with_ext
            data.file_ext,                                   # be consistent (e.g., ".mp3")
            data.content_type or "application/octet-stream",
            data.object_key,
            now, now,
        )

    async def _update_fields(self, file_id: str, **fields) -> None:
        # add updated_at automatically
        fields["updated_at"] = datetime.now(timezone.utc)

        if not fields:
            return
        sets = []
        args = []
        i = 1
        for k, v in fields.items():
            sets.append(f"{k} = ${i}")
            args.append(v)
            i += 1
        args.append(file_id)
        sql = f"UPDATE transcriptions SET {', '.join(sets)} WHERE file_id = ${i}"
        await store.client.execute_command(sql, *args)

    def _duration_seconds_from_bytes(self, b: bytes) -> float | None:
        import os
        import tempfile
        try:
            from mutagen import File as MutagenFile
        except ImportError:
            return None

        fd, p = tempfile.mkstemp(suffix=".audio")
        try:
            os.close(fd)
            with open(p, "wb") as f:
                f.write(b)
            mf = MutagenFile(p)
            if mf and getattr(mf, "info", None) and getattr(mf.info, "length", None):
                return float(mf.info.length)
            return None
        finally:
            try:
                os.remove(p)
            except OSError:
                pass

    async def _row_by_file_id(self, file_id: str) -> dict | None:
        row = await store.client.fetchrow(
            """
            SELECT id::text, file_id, filename, file_ext, content_type,
                   status, error, participants, transcription, full_text,
                   duration_seconds, created_at, updated_at
            FROM transcriptions
            WHERE file_id = $1
            """,
            file_id,
        )
        return dict(row) if row else None
    
    # ──────────────────────────────────────────────────────────────────────────────
    # Public API (same signatures you already use)
    # ──────────────────────────────────────────────────────────────────────────────
    async def save_audio(self, data: FileData, stream: BinaryIO = None) -> str:
            try:
                # Just create the database entry
                await self._insert_shell_if_missing(data)
                
                # We CANNOT calculate duration here anymore because we are not
                # loading the file. We will do it after FFmpeg conversion.
                
                await self._update_fields(
                    data.file_id,
                    status="in_progress",
                    # duration_seconds=duration, # <--- Removed, will update later
                )
                return data.file_id
            except Exception:
                logger.exception("STT: save_audio failed for %s", data.file_id)
                # ... error handling ...
                raise

    async def update_status(
        self,
        file_id: str,
        status: Literal["started","in_progress","running","transcribed","diarized","completed","failed"],
        job_id: Optional[str] = None,
        transcription: Optional[dict] = None,
        error: Optional[str] = None,
        participants: Optional[list[dict]] = None,
    ) -> None:
        try:
            patch: dict = {"status": status}
            if job_id is not None:
                patch["job_id"] = job_id
            if transcription is not None:
                patch["transcription"] = transcription
            if error is not None:
                patch["error"] = error
            if participants is not None:
                patch["participants"] = participants

            # ← FIX: pass kwargs
            await self._update_fields(file_id, **patch)
        except Exception:
            logger.exception("STT: update_status failed for %s", file_id)
            raise

    async def update_transcription(self, file_id: str, transcription: dict) -> None:
        logger.info("STT: update_transcription for %s (len=%s)", file_id, len(str(transcription)))
        await self.update_status(file_id, "completed", transcription=transcription)

    async def update_error(self, file_id: str, message: str) -> None:
        logger.info("STT: update_error for %s: %s", file_id, message)
        await self.update_status(file_id, "failed", error=message)

    # If you still want to fetch the raw audio bytes, wire it to your object store instead.
    async def get_file(self, file_id: str) -> BinaryIO:
        raise NotImplementedError("Raw audio is not stored in DB. Fetch from object storage instead.")

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
            # Return dict with keys your service expects
            return {
                "file_id": row.get("file_id"),
                "status": row.get("status"),
                "job_id": row.get("job_id"),
                "duration": row.get("duration_seconds"),
                "error": row.get("error"),
                "participants": row.get("participants"),
                "transcription": row.get("transcription"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
            }
        except Exception:
            logger.exception("STT: get_meta failed for %s", file_id)
            raise

    async def delete_audio(self, file_id: str) -> None:
        logger.info("STT: delete_audio noop (not storing raw bytes) for %s", file_id)

    async def insert_meta(self, data: FileData) -> None:
        await self._insert_shell_if_missing(data)

    async def load_audio(self, file_id: str) -> bytes:
            # Prevent usage of this method if possible, or force streaming download
            # If you truly need bytes, fetch from OCI, but try to avoid calling this.
            row = await self._row_by_file_id(file_id)
            object_key = row.get("object_key") if row else None
            
            if object_key:
                # Ideally, return a stream, not bytes. 
                # If you must return bytes, this WILL consume RAM.
                return await store.objects.get_bytes(object_key) 

            raise RuntimeError("Audio bytes unavailable.")
    
    async def get_audio_url(self, file_id: str) -> str:
        row = await store.client.fetchrow(
            "SELECT object_key FROM transcriptions WHERE file_id = $1", 
            file_id
        )
        if not row or not row["object_key"]:
            raise RuntimeError(f"Database has no object_key for file {file_id}")
            
        object_key = row["object_key"]
        url = await asyncio.to_thread(get_read_url, object_key)
        
        return url
