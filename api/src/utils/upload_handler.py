from __future__ import annotations

import os
import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict

ENV = os.getenv("APP_ENV", "prod").lower()

# Always export these (other modules import them)
osc = None
NAMESPACE = ""
BUCKET = os.getenv("AZURE_STORAGE_CONTAINER", "")  # container

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _mk_object_key(filename: str) -> str:
    now = _utc_now()
    return f"{now:%Y/%m/%d}/{uuid.uuid4()}-{filename}"

def _missing() -> RuntimeError:
    return RuntimeError(
        "Azure storage is not configured. "
        "Require AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY, AZURE_STORAGE_CONTAINER."
    )

AZ_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
AZ_KEY = os.getenv("AZURE_STORAGE_KEY", "")
BUCKET = os.getenv("AZURE_STORAGE_CONTAINER", "")
AZ_ENDPOINT = os.getenv("AZURE_BLOB_ENDPOINT", "") or (f"https://{AZ_ACCOUNT}.blob.core.windows.net" if AZ_ACCOUNT else "")

def _ensure_config() -> None:
    if not (AZ_ACCOUNT and AZ_KEY and BUCKET and AZ_ENDPOINT):
        raise _missing()

# --- Azure SDK imports only if we have config OR if you prefer always installed ---
# We keep them inside to avoid startup import errors in environments without azure libs.
def _blob_url(blob_name: str) -> str:
    _ensure_config()
    return f"{AZ_ENDPOINT}/{BUCKET}/{blob_name}"

def _sas(
    blob_name: str,
    minutes: int,
    *,
    read: bool = False,
    write: bool = False,
    create: bool = False,
) -> str:
    _ensure_config()
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions

    return generate_blob_sas(
        account_name=AZ_ACCOUNT,
        account_key=AZ_KEY,
        container_name=BUCKET,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=read, write=write, create=create),
        expiry=_utc_now() + timedelta(minutes=minutes),
    )

def get_read_url(object_name: str, minutes: int = 60) -> str:
    """
    Read-only SAS URL for streaming / ffmpeg.
    """
    return f"{_blob_url(object_name)}?{_sas(object_name, minutes, read=True)}"

def _put_sas_url(object_name: str, minutes: int = 15) -> str:
    """
    PUT SAS URL. Client must send: x-ms-blob-type: BlockBlob
    """
    return f"{_blob_url(object_name)}?{_sas(object_name, minutes, write=True, create=True)}"

def _create_session(filename: str, size: int, content_type: str) -> Dict[str, Any]:
    _ensure_config()
    object_key = _mk_object_key(filename)
    return {
        "object_key": object_key,
        "upload_url": _put_sas_url(object_key),
        # IMPORTANT: required for Azure PUT-to-Blob
        "upload_headers": {
            "x-ms-blob-type": "BlockBlob",
            # content-type is optional but useful
            "Content-Type": content_type or "application/octet-stream",
        },
        "presigned_urls": [],
        "part_size": None,
        "complete_url": None,
    }

async def make_multipart_session(filename: str, size: int, content_type: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _create_session, filename, size, content_type)

async def open_object_stream(key: str):
    """
    Returns an Azure StreamingDownloader (download_blob()).
    """
    _ensure_config()
    from azure.storage.blob import BlobClient

    def _open_stream_sync():
        bc = BlobClient(
            account_url=AZ_ENDPOINT,
            container_name=BUCKET,
            blob_name=key,
            credential=AZ_KEY,
        )
        return bc.download_blob()

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _open_stream_sync)