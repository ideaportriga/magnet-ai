"""File transfer helpers for Teams note-taker.

This module contains HTTP download probing and multipart upload helpers to keep
`note_taker.py` focused on bot logic.
"""

import base64
import datetime as dt
import hashlib
import mimetypes
from logging import getLogger
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict
from urllib.parse import parse_qs, urlparse

import httpx

from utils import upload_handler

from .note_taker_utils import (
    _build_note_taker_filename,
    _get_meeting_id_part,
    _guess_filename_from_link,
    _parse_content_disposition_filename,
    _parse_content_length,
)

logger = getLogger(__name__)


async def _download_file_from_link(
    link: str, token: str | None, meeting: Dict[str, Any] | None = None
) -> tuple[str, dict[str, str], Callable[[str, str | None, str], tuple[str, str]]]:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    file_urls = (
        query.get("fileUrl")
        or query.get("fileurl")
        or query.get("file_url")
        or query.get("file")
    )
    if file_urls:
        link = file_urls[0]
        parsed = urlparse(link)

    headers: dict[str, str] = {}
    # TODO: before sending the token ensure it is teams.microsoft.com or sharepint.com
    if token:
        headers["Authorization"] = f"Bearer {token}"

    download_url = link
    # If it's a SharePoint/OneDrive URL, go via Graph /shares
    # TODO: include sharepoint-df.com and 1drv.ms
    if parsed.netloc.endswith("sharepoint.com") or "d.docs.live.net" in parsed.netloc:
        raw_url = link
        # base64url encode WITHOUT padding
        share_id = "u!" + base64.urlsafe_b64encode(raw_url.encode("utf-8")).decode(
            "ascii"
        ).rstrip("=")
        graph_download_url = (
            f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
        )
        download_url = graph_download_url

    def _name_resolver(
        content_type: str, content_disposition: str | None, final_url: str
    ) -> tuple[str, str]:
        filename = _parse_content_disposition_filename(content_disposition)
        if not filename:
            filename = _guess_filename_from_link(final_url or link)

        path = Path(filename)
        ext = path.suffix
        if not ext:
            guessed_ext = mimetypes.guess_extension(content_type) or ".bin"
            ext = guessed_ext

        meeting_part = _get_meeting_id_part(meeting)
        source_key = final_url or link
        item_hash = hashlib.sha1(source_key.encode("utf-8")).hexdigest()[:12]
        date_part = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
        final_name = _build_note_taker_filename(
            kind="file",
            meeting_id=meeting_part,
            item_id=item_hash,
            date_part=date_part,
            ext=ext,
        )
        return Path(final_name).stem, Path(final_name).suffix or ext

    return download_url, headers, _name_resolver


async def _probe_remote_file_metadata(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str],
) -> tuple[int | None, str | None, str | None, str]:
    """
    Best-effort probe for size/content headers without downloading the full file.
    Returns: (size_bytes, content_type, content_disposition, final_url)
    """
    # 1) HEAD (preferred if supported)
    try:
        head_resp = await client.head(url, headers=headers)
        if head_resp.status_code < 400:
            size = _parse_content_length(head_resp.headers.get("Content-Length"))
            content_type = head_resp.headers.get("Content-Type")
            content_disposition = head_resp.headers.get("Content-Disposition")
            final_url = str(head_resp.url) if head_resp.url else url
            return size, content_type, content_disposition, final_url
    except httpx.HTTPError:
        pass

    # 2) Range request to retrieve total size via Content-Range.
    range_headers = {**headers, "Range": "bytes=0-0"}
    try:
        async with client.stream("GET", url, headers=range_headers) as resp:
            if resp.status_code >= 400:
                resp.raise_for_status()
            content_range = resp.headers.get("Content-Range")
            total_size = None
            if content_range and "/" in content_range:
                raw_total = content_range.split("/")[-1]
                if raw_total.isdigit():
                    total_size = int(raw_total)
            size = total_size or _parse_content_length(
                resp.headers.get("Content-Length")
            )
            content_type = resp.headers.get("Content-Type")
            content_disposition = resp.headers.get("Content-Disposition")
            final_url = str(resp.url) if resp.url else url
            return size, content_type, content_disposition, final_url
    except httpx.HTTPError:
        pass

    return None, None, None, url


async def _upload_part(
    client: httpx.AsyncClient,
    url: str,
    data: bytes,
    headers: dict[str, str],
) -> str:
    part_headers = dict(headers)
    part_headers["Content-Length"] = str(len(data))
    response = await client.put(url, content=data, headers=part_headers)
    response.raise_for_status()
    etag = response.headers.get("ETag") or response.headers.get("etag") or ""
    return etag.strip('"')


async def _complete_multipart_upload(
    client: httpx.AsyncClient,
    complete_url: str,
    parts: list[dict[str, Any]],
) -> None:
    response = await client.post(complete_url, json={"parts": parts})
    response.raise_for_status()


async def _upload_stream_to_object(
    *,
    stream: AsyncIterator[bytes],
    size: int,
    content_type: str,
    filename: str,
) -> str:
    session = await upload_handler.make_multipart_session(
        filename=filename,
        size=size,
        content_type=content_type,
    )

    object_key = (session or {}).get("object_key")
    upload_url = (session or {}).get("upload_url") or (session or {}).get("url")
    upload_headers: dict[str, str] = (session or {}).get("upload_headers") or {}
    presigned_urls = (session or {}).get("presigned_urls") or []
    part_size_raw = (session or {}).get("part_size")
    try:
        part_size = int(part_size_raw) if part_size_raw else None
    except (TypeError, ValueError):
        part_size = None
    complete_url = (session or {}).get("complete_url")

    if not object_key:
        raise RuntimeError("Upload session did not return an object key.")

    logger.info("[teams note-taker] streaming upload to object: %s", object_key)

    timeout = httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        use_multipart = False
        if presigned_urls:
            if len(presigned_urls) == 1 and not part_size and not complete_url:
                upload_url = upload_url or presigned_urls[0]
            else:
                use_multipart = True

        if use_multipart:
            if not part_size:
                raise RuntimeError("Multipart upload session missing part size.")
            if not complete_url:
                raise RuntimeError("Multipart upload session missing completion URL.")

            parts: list[dict[str, Any]] = []
            buffer = bytearray()
            part_index = 0

            async for chunk in stream:
                if not chunk:
                    continue
                buffer.extend(chunk)
                while len(buffer) >= part_size:
                    if part_index >= len(presigned_urls):
                        raise RuntimeError(
                            "Multipart upload session provided insufficient part URLs."
                        )
                    data = bytes(buffer[:part_size])
                    del buffer[:part_size]
                    etag = await _upload_part(
                        client, presigned_urls[part_index], data, upload_headers
                    )
                    parts.append({"part_number": part_index + 1, "etag": etag})
                    part_index += 1

            if buffer:
                if part_index >= len(presigned_urls):
                    raise RuntimeError(
                        "Multipart upload session provided insufficient part URLs."
                    )
                etag = await _upload_part(
                    client, presigned_urls[part_index], bytes(buffer), upload_headers
                )
                parts.append({"part_number": part_index + 1, "etag": etag})
                part_index += 1

            if part_index != len(presigned_urls):
                raise RuntimeError(
                    "Multipart upload session returned unexpected part URLs."
                )

            await _complete_multipart_upload(client, complete_url, parts)
            return object_key

        if not upload_url:
            raise RuntimeError("Upload session missing upload URL.")

        upload_headers = {
            "Content-Type": content_type,
            "Content-Length": str(size),
            **upload_headers,
        }

        response = await client.put(upload_url, content=stream, headers=upload_headers)
        response.raise_for_status()

    return object_key
