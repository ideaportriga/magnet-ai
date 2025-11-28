import os
import asyncio
import json
import time
from io import BytesIO
from typing import Dict, List, BinaryIO

import oci.ai_speech.models as oci_models
from oci.ai_speech import AIServiceSpeechClient
from oci.object_storage import ObjectStorageClient
from oci.object_storage.models import CreateBucketDetails

from ..base import BaseTranscriber
from ...models import TranscriptionCfg
from ...storage.postgres_storage import PgDataStorage


OCI_ENV = {
    k: os.getenv(k, "")
    for k in (
        "OCI_USER_OCID_FRANKFURT_1",
        "OCI_TENANCY_OCID_FRANKFURT_1",
        "OCI_REGION_FRANKFURT_1",
        "OCI_FINGERPRINT_FRANKFURT_1",
        "OCI_PRIVATE_KEY_PATH_FRANKFURT_1",
        "OCI_COMPARTMENT_OCID_FRANKFURT_1",
        "OCI_BUCKET_NAME_FRANKFURT_1",
    )
}
# TODO - rework env variable handling
# if not all(OCI_ENV.values()):
#     raise RuntimeError("One or more required OCI_* variables are missing")

OCI_CONFIG = {
    "user": OCI_ENV["OCI_USER_OCID_FRANKFURT_1"],
    "tenancy": OCI_ENV["OCI_TENANCY_OCID_FRANKFURT_1"],
    "region": OCI_ENV["OCI_REGION_FRANKFURT_1"],
    "fingerprint": OCI_ENV["OCI_FINGERPRINT_FRANKFURT_1"],
    "key_file": OCI_ENV["OCI_PRIVATE_KEY_PATH_FRANKFURT_1"],
}


class OracleSpeechTranscriber(BaseTranscriber):
    """
    Speech-to-text via OCI AI Speech, streaming upload (no temp files),
    with diarization disabled so that downstream modules can handle speaker
    segmentation independently.
    """

    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)
        self._speech = AIServiceSpeechClient(OCI_CONFIG)
        self._os_client = ObjectStorageClient(OCI_CONFIG)
        self._storage = storage
        self._bucket = OCI_ENV["OCI_BUCKET_NAME_FRANKFURT_1"]
        self._comp_id = OCI_ENV["OCI_COMPARTMENT_OCID_FRANKFURT_1"]
        self._granularity = (cfg.internal_cfg or {}).get("granularity", "word")
        self._namespace = self._os_client.get_namespace().data
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        buckets = self._os_client.list_buckets(self._namespace, self._comp_id).data
        if not any(b.name == self._bucket for b in buckets):
            self._os_client.create_bucket(
                self._namespace,
                CreateBucketDetails(name=self._bucket, compartment_id=self._comp_id),
            )

    async def _get_audio(self, file_id: str) -> BytesIO:
        buf: BytesIO = await self._storage.get_file(file_id)
        buf.seek(0)
        buf.name = f"{file_id}.mp3"
        return buf

    def _submit_job(self, object_name: str, file_stream: BinaryIO) -> str:
        self._os_client.put_object(
            namespace_name=self._namespace,
            bucket_name=self._bucket,
            object_name=object_name,
            put_object_body=file_stream,
        )

        details = oci_models.CreateTranscriptionJobDetails(
            display_name=f"{object_name}_job",
            compartment_id=self._comp_id,
            input_location=oci_models.ObjectListInlineInputLocation(
                location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
                object_locations=[
                    oci_models.ObjectLocation(
                        namespace_name=self._namespace,
                        bucket_name=self._bucket,
                        object_names=[object_name],
                    )
                ],
            ),
            output_location=oci_models.OutputLocation(
                namespace_name=self._namespace,
                bucket_name=self._bucket,
            ),
            additional_transcription_formats=["SRT"],
            model_details=oci_models.TranscriptionModelDetails(
                model_type=self._tr_cfg.model.upper(),
                domain="GENERIC",
            ),
        )
        resp = self._speech.create_transcription_job(
            create_transcription_job_details=details
        )
        return resp.data.id

    def _wait_for_job(self, job_id: str, poll=10, timeout=20 * 60):
        t0 = time.time()
        while True:
            job = self._speech.get_transcription_job(job_id).data
            if job.lifecycle_state in ("SUCCEEDED", "FAILED", "CANCELED"):
                if job.lifecycle_state != "SUCCEEDED":
                    raise RuntimeError(f"OCI job ended with {job.lifecycle_state}")
                return job
            if time.time() - t0 > timeout:
                raise TimeoutError("OCI transcription job timed out")
            time.sleep(poll)

    def _fetch_output(self, job) -> dict:
        prefix = job.output_location.prefix or f"jobs/{job.id}/"
        for _ in range(6):
            objs = (
                self._os_client.list_objects(
                    namespace_name=self._namespace,
                    bucket_name=self._bucket,
                    prefix=prefix,
                ).data.objects
                or []
            )
            for obj in objs:
                if obj.name.lower().endswith(".json"):
                    body = self._os_client.get_object(
                        namespace_name=self._namespace,
                        bucket_name=self._bucket,
                        object_name=obj.name,
                    ).data.content
                    return json.loads(body)
            time.sleep(5)
        raise RuntimeError(f"No JSON output found after job {job.id}")

    async def _transcribe(self, file_id: str) -> Dict:
        raw = await self._get_audio(file_id)

        def _blocking() -> Dict:
            raw.seek(0)
            job = self._wait_for_job(self._submit_job(raw.name, raw))
            res_json = self._fetch_output(job)

            text_parts: List[str] = []
            segments: List[dict] = []

            for t in res_json["transcriptions"]:
                text_parts.append(t["transcription"])

            for tok in res_json["transcriptions"][0]["tokens"]:
                if tok["type"] != "WORD":
                    continue
                segments.append(
                    {
                        "start": self._to_seconds(tok["startTime"]),
                        "end": self._to_seconds(tok["endTime"]),
                        "text": tok["token"],
                    }
                )

            return {"text": " ".join(text_parts), "segments": segments}

        return await asyncio.to_thread(_blocking)

    @staticmethod
    def _to_seconds(timestr: str) -> float:
        timestr = timestr.strip().lower()
        if timestr.endswith("ms"):
            return float(timestr[:-2]) / 1000.0
        if timestr.endswith("s"):
            return float(timestr[:-1])
        return float(timestr)
