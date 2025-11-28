from __future__ import annotations

import asyncio
from io import BytesIO
from typing import BinaryIO, Literal

from .models import FileData
from .storage.postgres_storage import PgDataStorage
from .pipeline_factory import build_pipeline
from .pipeline import TranscriptionPipeline
from .transcribe.base import _assert_supported
from utils.upload_handler import open_object_stream, osc, NAMESPACE, BUCKET
import oci

storage = PgDataStorage()
_RUNNING: dict[str, asyncio.Task[None]] = {}

PipelineKind = Literal[
    "mock",
    "whisper-mock",
    "whisper-pyannote",
    "oracle-mock",
    "whisper-http",
    "whisper-http-pyannote",
    "elevenlabs",
    "azure-whisper-azure-diar",
    "oci-whisper-oci-diar",
]


async def _wait_until_exists(
    key: str,
    wait_timeout: float = 30.0,
    every: float = 0.5,
) -> None:
    waited = 0.0
    while waited < wait_timeout:
        try:
            osc.head_object(NAMESPACE, BUCKET, key)
            return
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                await asyncio.sleep(every)
                waited += every
            else:  # any other OCI error → re-raise
                raise
    raise RuntimeError(f"Object {key!r} not visible after {wait_timeout}s")


# ─────────────────────────────────────────────────────────────
# public entry-point
# ─────────────────────────────────────────────────────────────
async def submit(
    name: str,
    ext: str,
    bytes_: bytes | None = None,
    *,
    object_key: str | None = None,
    content_type: str = "application/octet-stream",
    backend: PipelineKind = "mock",
    language: str | None = None,
    number_of_participants: str | None = None,
) -> str:
    if bytes_ is None and object_key is None:
        raise ValueError("submit(): supply either bytes_ or object_key")

    _assert_supported(f".{ext}")

    file_data = FileData(
        file_name=name,
        file_ext=f".{ext}",
        content_type=content_type,
        object_key=object_key,
    )

    # Decide where to read the bytes from
    if bytes_ is not None:
        stream: BinaryIO = BytesIO(bytes_)
    else:
        await _wait_until_exists(object_key)  # ← NEW
        stream = await open_object_stream(object_key)

    # Build pipeline and launch
    pipeline: TranscriptionPipeline = build_pipeline(
        backend,
        storage,
        language=language,
        number_of_participants=number_of_participants,
    )

    task = asyncio.create_task(
        _run_pipeline_and_cleanup(pipeline, file_data, stream),
        name=file_data.file_id,
    )
    _RUNNING[file_data.file_id] = task
    return file_data.file_id


# convenience accessors (unchanged) -----------------------------------------
async def get_status(file_id: str) -> str | None:
    meta = await storage.get_meta(file_id)
    return (meta or {}).get("status")


async def get_error(file_id: str) -> str | None:
    meta = await storage.get_meta(file_id)
    return (meta or {}).get("error")


async def get_transcription(file_id: str):
    meta = await storage.get_meta(file_id)
    return (meta or {}).get("transcription")


async def _delete_object_if_needed(file_data: FileData) -> None:
    # dev mode: osc is None → do nothing
    if osc is None:
        return

    if not file_data.object_key:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        osc.delete_object,
        NAMESPACE,
        BUCKET,
        file_data.object_key,
    )


async def _run_pipeline_and_cleanup(
    pipeline: TranscriptionPipeline,
    file_data: FileData,
    stream: BinaryIO,
) -> None:
    try:
        await pipeline.run(file_data, stream)
    finally:
        # Best-effort close of the stream
        try:
            if hasattr(stream, "close"):
                stream.close()
        except Exception:
            pass

        # Delete remote object (only if object_key + osc)
        await _delete_object_if_needed(file_data)
