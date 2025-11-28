from __future__ import annotations

from datetime import datetime, UTC
from typing import BinaryIO, Optional, Literal
from dataclasses import fields
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from db import get_database_client
from ..models import FileData
from ..services.ffmpeg import get_audio_duration


class MongoDataStorage:
    AUDIO_BUCKET = "audio"

    def __init__(self) -> None:
        db_client = get_database_client()
        self.db = db_client.database
        self.fs = AsyncIOMotorGridFSBucket(self.db, bucket_name=self.AUDIO_BUCKET)
        # self.meta = self.db["transcription_meta"]
        self.recordings = self.db["recordings"]

    async def save_audio(self, data: FileData, stream: BinaryIO) -> str:
        """
        Store the bytes under the SAME ObjectId that FileData already uses.
        That way load_audio(file_id) will later find the file.
        """
        oid = ObjectId(data.file_id)
        await self.fs.upload_from_stream_with_id(
            oid,
            data.filename_with_ext,
            stream,
            metadata={"contentType": data.content_type or "application/octet-stream"},
        )
        await self.set_audio_duration(str(oid))
        return str(oid)

    async def set_audio_duration(self, file_id: str) -> None:
        try:
            duration = await get_audio_duration(self.fs, file_id)
            print(f"Audio duration for {file_id}: {duration}")
            await self.recordings.update_one(
                {"file_id": file_id}, {"$set": {"duration": duration}}
            )
        except Exception as e:
            print(f"Failed to get audio duration for {file_id}: {e}")
            await self.recordings.update_one(
                {"file_id": file_id}, {"$set": {"duration": 0.0}}
            )

    async def load_audio(self, file_id: str) -> bytes:
        """
        Read the file back out of GridFS.  Two awaits:
            1. open_download_stream -> AsyncIOMotorGridOut
            2. grid_out.read()      -> bytes
        """
        oid = ObjectId(file_id)
        grid_out = await self.fs.open_download_stream(oid)
        return await grid_out.read()

    async def insert_meta(self, data: FileData) -> None:
        update_fields = {
            "content_type": data.content_type,
            "file_ext": data.file_ext,
            "metadata.updated_at": datetime.now(UTC),
        }
        await self.recordings.update_one(
            {"file_id": data.file_id}, {"$set": update_fields}
        )

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
        update_fields: dict = {
            "status": status,
            "metadata.updated_at": datetime.now(UTC),
        }
        if job_id is not None:
            update_fields["job_id"] = job_id
        if transcription is not None:
            update_fields["transcription"] = transcription
        if error is not None:
            update_fields["error"] = error
        if participants is not None:
            update_fields["participants"] = participants

        # await self.meta.update_one({"file_id": file_id}, {"$set": update_fields})
        await self.recordings.update_one({"file_id": file_id}, {"$set": update_fields})

    async def update_job(
        self, file_id: str, status: str, job_id: Optional[str] = None
    ) -> None:
        await self.update_status(file_id, status, job_id=job_id)

    async def update_transcription(self, file_id: str, transcription: dict) -> None:
        await self.update_status(file_id, "completed", transcription=transcription)

    async def get_meta(self, file_id: str) -> FileData:
        doc = await self.recordings.find_one({"file_id": file_id}) or {}

        allowed = {f.name for f in fields(FileData)}
        clean = {k: v for k, v in doc.items() if k in allowed}
        return FileData(**clean)

    async def save(self, file_data: FileData, file_stream: BinaryIO) -> str:
        """Store bytes and metadata in one call (compat with SQL storage)."""
        await self.save_audio(file_data, file_stream)
        await self.insert_meta(file_data)
        return file_data.file_id

    async def get_file(self, file_id: str) -> BinaryIO:
        """Return a new binary stream for the stored audio."""
        from io import BytesIO

        return BytesIO(await self.load_audio(file_id))

    async def get_transcription(self, file_id: str) -> Optional[dict]:
        meta = await self.get_meta(file_id)
        return getattr(meta, "transcription", None)

    async def update(self, file_id: str, **fields) -> None:
        """Generic partial-update (some old code calls storage.update)."""
        fields["metadata.updated_at"] = datetime.now(UTC)
        await self.recordings.update_one({"file_id": file_id}, {"$set": fields})

    async def update_error(self, file_id: str, message: str) -> None:
        """Store an error message and mark the job as failed."""
        await self.update_status(file_id, "failed", error=message)

    async def delete_audio(self, file_id: str) -> None:
        try:
            await self.fs.delete(ObjectId(file_id))
        except Exception as e:
            print(f"delete_audio failed for {file_id}: {e}")
