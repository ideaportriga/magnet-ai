from __future__ import annotations
import abc
import asyncio
import uuid
from typing import BinaryIO
import os

from ..models import FileData, TranscriptionCfg
from ..storage.postgres_storage import PgDataStorage


ALLOWED_EXT = {".flac", ".m4a", ".mp3", ".ogg", ".wav", ".webm", ".mp4"}


def _assert_supported(ext: str) -> None:
    """Raise if extension not in the allow-list."""
    if ext.lower() not in ALLOWED_EXT:
        raise ValueError(f"Unsupported audio format: {ext}")


class TranscriptionJob:
    """A tiny handle to track an async transcription job."""

    def __init__(self, *, file_id: str, job_id: str, task: asyncio.Task[None]):
        self.file_id = file_id
        self.job_id = job_id
        self._task = task

    @property
    def done(self) -> bool:
        return self._task.done()

    async def wait(self) -> None:
        await self._task


class BaseTranscriber(abc.ABC):
    """Async interface for concrete transcribers."""

    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        self._storage = storage
        self._cfg = cfg

    async def submit(
        self, file_data: FileData, file_stream: BinaryIO
    ) -> TranscriptionJob:
        if not getattr(file_stream, "name", None):
            file_stream.name = file_data.filename_with_ext  # e.g. "demo.mp3"

        _, ext = os.path.splitext(file_stream.name)
        _assert_supported(ext)
        file_id = await self._storage.save(file_data, file_stream)

        job_id = uuid.uuid4().hex
        task = asyncio.create_task(self._process(file_id), name=f"job-{job_id}")

        await self._storage.update(file_id, status="started", job_id=job_id)

        return TranscriptionJob(file_id=file_id, job_id=job_id, task=task)

    async def _process(self, file_id: str) -> None:
        try:
            await self._storage.update(file_id, status="in_progress")

            transcription = await self._transcribe(file_id)
            await self._storage.update_transcription(file_id, transcription)

            await self._storage.update(file_id, status="completed")
        except Exception as exc:
            await self._storage.update(file_id, status="failed", error=str(exc))
            raise

    @abc.abstractmethod
    async def _transcribe(self, file_id: str) -> dict:
        """Return {"text": "...", "segments": [...] }."""
