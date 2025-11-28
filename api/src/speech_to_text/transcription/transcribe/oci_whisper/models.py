from __future__ import annotations
import os
import time
import json
import asyncio
from io import BytesIO
from typing import Dict, Any

import oci.ai_speech.models as oci_models
from oci.ai_speech import AIServiceSpeechClient
from oci.object_storage import ObjectStorageClient

from ..base import BaseTranscriber
from ...storage.postgres_storage import PgDataStorage
from ...models import TranscriptionCfg

_OCI_CACHE: dict[str, Dict[str, Any]] = {}


def _cache_payload(file_id: str, payload: Dict[str, Any]):
    _OCI_CACHE[file_id] = payload


def drain_oci_cached_payload(file_id: str) -> Dict[str, Any] | None:
    return _OCI_CACHE.pop(file_id, None)


OCI_USER_OCID = os.getenv("OCI_USER_OCID_FRANKFURT_1", "")
OCI_TENANCY_OCID = os.getenv("OCI_TENANCY_OCID_FRANKFURT_1", "")
OCI_REGION = os.getenv("OCI_REGION_FRANKFURT_1", "")
OCI_FINGERPRINT = os.getenv("OCI_FINGERPRINT_FRANKFURT_1", "")
OCI_PRIVATE_KEY_PATH = os.getenv("OCI_PRIVATE_KEY_PATH_FRANKFURT_1", "")
OCI_COMPARTMENT_OCID = os.getenv("OCI_COMPARTMENT_OCID_FRANKFURT_1", "")
OCI_BUCKET_NAME = os.getenv("OCI_BUCKET_NAME_FRANKFURT_1", "")

# TODO - rework env variable handling
# if not all([OCI_USER_OCID, OCI_TENANCY_OCID, OCI_REGION, OCI_FINGERPRINT, OCI_PRIVATE_KEY_PATH, OCI_COMPARTMENT_OCID, OCI_BUCKET_NAME]):
#     raise RuntimeError("Missing one or more OCI_* env vars")

OCI_CONFIG = {
    "user": OCI_USER_OCID,
    "tenancy": OCI_TENANCY_OCID,
    "region": OCI_REGION,
    "fingerprint": OCI_FINGERPRINT,
    "key_file": OCI_PRIVATE_KEY_PATH,
}
DEFAULT_OCI_WHISPER_MODEL = os.getenv("OCI_WHISPER_MODEL", "WHISPER_MEDIUM")


class OciWhisperTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)
        self._model_type = (cfg.internal_cfg or {}).get(
            "model_type", DEFAULT_OCI_WHISPER_MODEL
        )
        self._speech = AIServiceSpeechClient(OCI_CONFIG)
        self._os = ObjectStorageClient(OCI_CONFIG)
        self._bucket = OCI_BUCKET_NAME
        self._namespace = self._os.get_namespace().data

    async def _get_audio(self, file_id: str) -> BytesIO:
        buf: BytesIO = await self._storage.get_file(file_id)
        buf.seek(0)
        meta = await self._storage.get_meta(file_id)
        ext = getattr(meta, "file_ext", None) or ".audio"
        buf.name = f"{file_id}{ext}"
        return buf

    async def _transcribe(self, file_id: str) -> dict:
        raw = await self._get_audio(file_id)

        def _run() -> Dict[str, Any]:
            obj = raw.name
            raw.seek(0)
            self._os.put_object(self._namespace, self._bucket, obj, raw)

            n_speakers = _as_int_or_none(
                getattr(self._cfg, "number_of_participants", None)
            )

            lang = (self._cfg.language or "").strip().lower()
            if not lang or lang in {"other", "auto"}:
                lang = "auto"

            details = oci_models.CreateTranscriptionJobDetails(
                display_name=f"{obj}_whisper_diar",
                compartment_id=OCI_COMPARTMENT_OCID,
                input_location=oci_models.ObjectListInlineInputLocation(
                    location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
                    object_locations=[
                        oci_models.ObjectLocation(
                            namespace_name=self._namespace,
                            bucket_name=self._bucket,
                            object_names=[obj],
                        )
                    ],
                ),
                output_location=oci_models.OutputLocation(
                    namespace_name=self._namespace, bucket_name=self._bucket
                ),
                model_details=oci_models.TranscriptionModelDetails(
                    model_type=self._model_type,
                    domain="GENERIC",
                    language_code=lang,
                    transcription_settings=oci_models.TranscriptionSettings(
                        diarization=oci_models.Diarization(
                            is_diarization_enabled=True,
                            number_of_speakers=n_speakers,
                        ),
                    ),
                ),
            )
            job_id = self._speech.create_transcription_job(details).data.id
            job = self._wait(job_id)
            payload = self._fetch(job)

            parsed_result = _parse_oci_payload(payload)
            _cache_payload(file_id, parsed_result)
            return parsed_result

        return await asyncio.to_thread(_run)

    def _wait(self, job_id: str, poll=8, timeout=30 * 60):
        t0 = time.time()
        while True:
            job = self._speech.get_transcription_job(job_id).data
            if job.lifecycle_state in ("SUCCEEDED", "FAILED", "CANCELED"):
                if job.lifecycle_state != "SUCCEEDED":
                    raise RuntimeError(f"OCI job failed: {job.lifecycle_state}")
                return job
            if time.time() - t0 > timeout:
                raise TimeoutError("OCI job timed out")
            time.sleep(poll)

    def _fetch(self, job) -> Dict[str, Any]:
        prefix = job.output_location.prefix or f"jobs/{job.id}/"
        for _ in range(10):
            objs = (
                self._os.list_objects(
                    self._namespace, self._bucket, prefix=prefix
                ).data.objects
                or []
            )
            for o in objs:
                if o.name.lower().endswith(".json"):
                    data = self._os.get_object(
                        self._namespace, self._bucket, o.name
                    ).data.content
                    return json.loads(data)
            time.sleep(5)
        raise RuntimeError("No JSON found")


def _to_sec(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace("s", "")
    try:
        return float(s)
    except Exception:
        return None


def _parse_oci_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    tr = (payload.get("transcriptions") or [{}])[0]
    full_text = tr.get("transcription", "")
    segments = []

    source_data = tr.get("tokens") or tr.get("words") or []

    for item in source_data:
        if "type" in item and (item.get("type") or "").upper() != "WORD":
            continue

        s = _to_sec(item.get("startTime") or item.get("start"))
        e = _to_sec(item.get("endTime") or item.get("end"))
        txt = item.get("text") or item.get("word") or item.get("token")

        spk = item.get("speakerIndex")
        if spk is None:
            spk = item.get("speakerLabel")
        if spk is None:
            spk = item.get("speaker_label")
        if spk is None:
            spk = item.get("speaker")

        spk_str = str(spk) if spk is not None else "speaker_unknown"

        if s is not None and e is not None and txt:
            segments.append({"start": s, "end": e, "text": txt, "speaker": spk_str})

    return {"text": full_text, "segments": segments}


def _as_int_or_none(v):
    if v is None:
        return None
    try:
        i = int(v)
        return i if i > 0 else None
    except (TypeError, ValueError):
        return None
