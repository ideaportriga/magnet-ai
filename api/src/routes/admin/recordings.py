from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from elevenlabs import AsyncElevenLabs
from litestar import Controller, get, post, Request
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException

from speech_to_text.transcription import service

MAX_UPLOAD_BYTES = 1000 * 1024 * 1024  # 1GB
DEFAULT_PIPELINE = "elevenlabs"


class RecordingsController(Controller):
    path = "/recordings"
    tags = ["Admin / Recordings"]

    @post("/")
    async def create_recording(self, request: Request) -> dict[str, Any]:
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
        number_of_participants: Optional[str] = None
        diarization_threshold: Optional[str] = None
        stt_model_system_name: Optional[str] = None
        keyterms = None
        entity_detection = None

        if ctype.startswith("multipart/"):
            form = await request.form()
            upload = form.get("file")
            object_key = form.get("object_key")
            filename = form.get("filename") or (upload.filename if upload else None)
            content_type = form.get("content_type") or (
                upload.content_type if upload else None
            )
            language = form.get("language")
            number_of_participants = form.get("number_of_participants")
            diarization_threshold = form.get("diarization_threshold")
            stt_model_system_name = form.get("stt_model_system_name")
            keyterms = form.getlist("keyterms") if form.get("keyterms") else None
            entity_detection = (
                form.getlist("entity_detection")
                if form.get("entity_detection")
                else None
            )
        else:
            data = await request.json()
            object_key = data.get("object_key")
            filename = data.get("filename")
            content_type = data.get("content_type")
            language = data.get("language")
            diarization_threshold = data.get("diarization_threshold")
            number_of_participants = data.get("number_of_participants")
            stt_model_system_name = data.get("stt_model_system_name")
            keyterms = data.get("keyterms")
            entity_detection = data.get("entity_detection")

        if not language:
            raise HTTPException(status_code=400, detail="'language' missing")

        if not stt_model_system_name:
            raise HTTPException(
                status_code=400, detail="'stt_model_system_name' missing"
            )

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

        def _is_provided(x: Optional[str]) -> bool:
            return (
                x is not None
                and str(x).strip() != ""
                and str(x).strip().lower() != "null"
            )

        if _is_provided(diarization_threshold):
            try:
                thr = float(diarization_threshold)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail="'diarization_threshold' must be a number",
                )

            if not (0.1 <= thr <= 0.4):
                raise HTTPException(
                    status_code=400,
                    detail="'diarization_threshold' must be in [0.1, 0.4]",
                )

            diarization_threshold = str(thr)

        file_bytes = None

        job_id = await service.submit(
            name=name_part,
            ext=ext,
            bytes_=file_bytes,
            object_key=object_key,
            content_type=content_type or "application/octet-stream",
            stt_model_system_name=stt_model_system_name,
            language=language,
            number_of_participants=number_of_participants,
            diarization_threshold=diarization_threshold,
            keyterms=keyterms,
            entity_detection=entity_detection,
        )

        return {
            "id": job_id,
            "source_file": name_part,
            "language": language,
            "stt_model_system_name": stt_model_system_name,
            "status": "started",
        }

    @get("/{job_id:str}")
    async def get_recording(self, job_id: str) -> dict[str, Any]:
        status = await service.get_status(job_id)
        result: dict[str, Any] = {"id": job_id, "status": status or "unknown"}
        if status == "failed":
            result["error"] = await service.get_error(job_id)
        elif status in {"transcribed", "completed", "diarized"}:
            tx = await service.get_transcription(job_id)
            result["transcription_job"] = tx
        return result

    @get("/{job_id:str}/status")
    async def recording_status(self, job_id: str) -> dict[str, Any]:
        st = await service.get_status(job_id)
        if st == "failed":
            err = await service.get_error(job_id)
            return {"status": st, "error": err or ""}
        return {"status": st or "unknown"}

    @get("/{job_id:str}/transcription")
    async def recording_transcription(self, job_id: str) -> dict[str, Any]:
        tx = await service.get_transcription(job_id)
        if tx is None:
            raise HTTPException(
                status_code=404, detail="Transcription not available yet"
            )
        return {"transcription": tx}

    @get("/scribe-token")
    async def scribe_token(self) -> dict[str, Any]:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")

        try:
            client = AsyncElevenLabs(api_key=api_key, timeout=30)
            token = await client.tokens.single_use.create("realtime_scribe")
            return token if isinstance(token, dict) else token.model_dump()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="ElevenLabs timed out")
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502, detail=f"ElevenLabs network error: {e}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create token: {e}")
