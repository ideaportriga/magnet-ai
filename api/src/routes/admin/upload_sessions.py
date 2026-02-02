from __future__ import annotations

from typing import Dict, Any
from litestar import Controller, post
from utils.upload_handler import make_multipart_session


class UploadSessionsController(Controller):
    path = "/upload-sessions"
    tags = ["Admin / Recordings"]

    @post("/", status_code=200)
    async def create_session(self, data: dict) -> Dict[str, Any]:
        """
        Expects:
        {
            "filename": "...",
            "size": 123,
            "type": "video/mp4"
        }

        Returns:
        {
            "object_key": "...",
            "upload_url": "...",
            "upload_headers": {"x-ms-blob-type": "BlockBlob", "Content-Type": "..."},
            "presigned_urls": [],
            "part_size": null,
            "complete_url": null
        }
        """
        return await make_multipart_session(
            filename=data["filename"],
            size=data["size"],
            content_type=data["type"],
        )
