from __future__ import annotations
from typing import Any, Optional

from litestar import Controller, get, post, Request
from litestar.exceptions import HTTPException
from litestar.datastructures import UploadFile

from speech_to_text.transcription import service

MAX_UPLOAD_BYTES = 1000 * 1024 * 1024  # 1GB
DEFAULT_PIPELINE = "elevenlabs"


class RecordingsController(Controller):
    path = "/recordings"
    tags = ["Admin / Recordings"]

    # ────────────────────────────────
    # POST /api/admin/recordings
    # ────────────────────────────────
    @post("/")
    async def create_recording(self, request: Request) -> dict[str, Any]:
        # Size guard (multipart only)
        if cl := request.headers.get("content-length"):
            try:
                if int(cl) > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File too large")
            except ValueError:
                pass

        ctype = request.headers.get("content-type", "")
        upload: UploadFile | None = None
        object_key: Optional[str] = None
        filename: Optional[str] = None
        content_type: Optional[str] = None
        language: Optional[str] = None
        pipeline_id: str = DEFAULT_PIPELINE
        number_of_participants: Optional[str] = None

        # Parse inputs
        if ctype.startswith("multipart/"):
            form = await request.form()
            upload = form.get("file")
            object_key = form.get("object_key")
            filename = form.get("filename") or (upload.filename if upload else None)
            content_type = form.get("content_type") or (
                upload.content_type if upload else None
            )
            language = form.get("language")
            pipeline_id = form.get("pipeline_id") or DEFAULT_PIPELINE
            number_of_participants = form.get("number_of_participants")
        else:
            data = await request.json()
            object_key = data.get("object_key")
            filename = data.get("filename")
            content_type = data.get("content_type")
            language = data.get("language")
            pipeline_id = data.get("pipeline_id") or DEFAULT_PIPELINE
            number_of_participants = data.get("number_of_participants")

        # Validate
        if not language:
            raise HTTPException(status_code=400, detail="'language' missing")
        if not (upload or object_key):
            raise HTTPException(status_code=400, detail="Need 'file' or 'object_key'")
        if not filename:
            raise HTTPException(status_code=400, detail="'filename' missing")

        try:
            name_part, ext = filename.rsplit(".", 1)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="filename must include extension"
            )

        file_bytes = await upload.read() if upload else None

        # Submit to transcription pipeline
        job_id = await service.submit(
            name=name_part,
            ext=ext,
            bytes_=file_bytes,
            object_key=object_key,
            content_type=content_type or "application/octet-stream",
            backend=pipeline_id,
            language=language,
            number_of_participants=number_of_participants,
        )

        # Return a lightweight job descriptor (no ORM)
        return {
            "id": job_id,
            "source_file": name_part,
            "language": language,
            "pipeline_id": pipeline_id,
            "status": "started",
        }

    # ────────────────────────────────
    # GET /api/admin/recordings/{job_id}
    # Optional convenience to fetch both status & (if ready) transcription
    # ────────────────────────────────
    @get("/{job_id:str}")
    async def get_recording(self, job_id: str) -> dict[str, Any]:
        status = await service.get_status(job_id)
        result: dict[str, Any] = {"id": job_id, "status": status or "unknown"}
        if status == "failed":
            result["error"] = await service.get_error(job_id)
        elif status in {"transcribed", "completed", "diarized"}:
            tx = await service.get_transcription(job_id)
            result["transcription"] = tx
        return result

    # ────────────────────────────────
    # GET /api/admin/recordings/{job_id}/status
    # ────────────────────────────────
    @get("/{job_id:str}/status")
    async def recording_status(self, job_id: str) -> dict[str, Any]:
        st = await service.get_status(job_id)
        if st == "failed":
            err = await service.get_error(job_id)
            return {"status": st, "error": err or ""}
        return {"status": st or "unknown"}

    # ────────────────────────────────
    # GET /api/admin/recordings/{job_id}/transcription
    # ────────────────────────────────
    @get("/{job_id:str}/transcription")
    async def recording_transcription(self, job_id: str) -> dict[str, Any]:
        tx = await service.get_transcription(job_id)
        if tx is None:
            # Not ready yet
            raise HTTPException(
                status_code=404, detail="Transcription not available yet"
            )
        return {"transcription": tx}
