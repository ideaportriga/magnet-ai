from __future__ import annotations
from typing import Dict, Any
from litestar import Controller, post
from utils.upload_handler import make_multipart_session


class UploadSessionsController(Controller):
    path = "/upload-sessions"
    tags = ["recordings"]

    @post("/", status_code=200)
    async def create_session(self, data: dict) -> Dict[str, Any]:
        """
        Expects  {"filename": ..., "size": ..., "type": ...}
        Returns  {"object_key": ..., "part_size": ..., "presigned_urls": [...], "complete_url": ...}
        """
        return await make_multipart_session(
            filename=data["filename"],
            size=data["size"],
            content_type=data["type"],
        )
