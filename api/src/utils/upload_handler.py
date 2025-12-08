from __future__ import annotations
import os
import asyncio
from datetime import datetime, timedelta
from io import BufferedReader
from pathlib import Path
import uuid

ENV = os.getenv("APP_ENV", "prod").lower()

# ===============================  DEV  =====================================
if ENV == "dev":
    LOCAL_DIR = Path("/tmp/uploads")
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[utils.oci] DEV mode → saving files to {LOCAL_DIR}")

    def _create_session(filename: str, *_):
        return {
            "object_key": filename,
            "upload_url": None,
            "presigned_urls": [],
            "part_size": None,
            "complete_url": None,
        }

    async def make_multipart_session(filename, size, content_type):
        return _create_session(filename, size, content_type)

    async def open_object_stream(key: str):
        return open(LOCAL_DIR / key, "rb")  # noqa: ASYNC230

    osc = None  # placeholder, not used in dev
    NAMESPACE = ""
    BUCKET = ""

# ===============================  PROD  ====================================
else:
    import oci
    from oci.object_storage.models import CreatePreauthenticatedRequestDetails

    cfg = {
        "user": os.getenv("OCI_USER_OCID_FRANKFURT_1"),
        "tenancy": os.getenv("OCI_TENANCY_OCID_FRANKFURT_1"),
        "region": os.getenv("OCI_REGION_FRANKFURT_1"),
        "fingerprint": os.getenv("OCI_FINGERPRINT_FRANKFURT_1"),
        "key_content": os.getenv(
            "OCI_PRIVATE_KEY_FRANKFURT_1"
        ),  # Changed from key_file
        "pass_phrase": os.getenv("OCI_PASSPHRASE_FRANKFURT_1") or None,
    }
    BUCKET = os.getenv("OCI_BUCKET_NAME_FRANKFURT_1", "")
    osc = oci.object_storage.ObjectStorageClient(cfg)
    NAMESPACE = osc.get_namespace().data

    def _put_par_url(object_name: str, minutes: int = 15) -> str:
        par = osc.create_preauthenticated_request(
            namespace_name=NAMESPACE,
            bucket_name=BUCKET,
            create_preauthenticated_request_details=CreatePreauthenticatedRequestDetails(
                name=f"put-{object_name}",
                object_name=object_name,
                access_type="ObjectWrite",
                time_expires=datetime.utcnow() + timedelta(minutes=minutes),
            ),
        ).data.access_uri
        return f"https://{osc.base_client.endpoint.lstrip('https://')}{par}"

    def _create_session(filename: str, *_):
        now = datetime.utcnow()
        object_key = f"uploads/{now:%Y/%m/%d}/{uuid.uuid4()}-{filename}"
        return {
            "object_key": object_key,
            "upload_url": _put_par_url(object_key),
            "presigned_urls": [],
            "part_size": None,
            "complete_url": None,
        }

    async def make_multipart_session(filename, size, content_type):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, _create_session, filename, size, content_type
        )

    def _open_stream_sync(key: str) -> BufferedReader:
        return osc.get_object(NAMESPACE, BUCKET, key).data.raw  # BinaryIO

    async def open_object_stream(key: str):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _open_stream_sync, key)
