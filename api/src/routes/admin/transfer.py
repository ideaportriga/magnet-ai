from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Annotated, Any

from litestar import Controller, Response, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT

from services.transfer import export_entities, import_entities

from sqlalchemy.ext.asyncio import AsyncSession

from storage import StorageService

logger = logging.getLogger(__name__)


class TransferController(Controller):
    path = "/transfer"
    tags = ["Admin / Transfer"]

    @post("/export/json", status_code=HTTP_200_OK)
    async def export_json(
        self,
        data: dict[str, Any] | None = None,
        skip_chunks: bool = False,
    ) -> dict[str, Any]:
        """Export data as JSON response"""
        result = await export_entities(data or {}, skip_chunks)

        return result

    @post("/export/file", status_code=HTTP_200_OK)
    async def export_file(
        self,
        data: dict[str, Any] | None = None,
        skip_chunks: bool = False,
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> Response[bytes]:
        """Export data as downloadable JSON file (also persisted as snapshot)."""
        result = await export_entities(data or {}, skip_chunks)

        timestamp = datetime.now().strftime("%Y_%m-%d:%H:%M:%S")
        filename = f"data_transfer_{timestamp}.json"
        content = json.dumps(result).encode("utf-8")

        # Persist snapshot in StorageService
        if storage_service and db_session:
            try:
                from uuid_utils import uuid7

                await storage_service.save_file(
                    db_session,
                    content=content,
                    filename=filename,
                    content_type="application/json",
                    entity_type="config_snapshot",
                    entity_id=uuid7(),
                    sub_path="snapshots/config",
                    extra={"trigger": "manual_export"},
                )
            except Exception:
                logger.exception("Failed to persist config snapshot")

        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @post("/import/json", status_code=HTTP_204_NO_CONTENT)
    async def import_json(
        self,
        data: dict[str, Any],
    ) -> None:
        """Import data from JSON payload"""
        if not data:
            raise ClientException("No import data")

        await import_entities(data)

    @post("/import/file", status_code=HTTP_204_NO_CONTENT)
    async def import_file(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        """Import data from uploaded JSON file (auto-snapshots current state before import)."""
        if not data:
            raise ClientException("No file uploaded")

        try:
            file_content = await data.read()
            import_data = json.loads(file_content)
        except json.JSONDecodeError:
            raise ClientException("Invalid JSON file")

        # Auto-snapshot current state before import (for rollback)
        if storage_service and db_session:
            try:
                from uuid_utils import uuid7

                current_state = await export_entities({}, skip_chunks=True)
                snapshot_content = json.dumps(current_state).encode("utf-8")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await storage_service.save_file(
                    db_session,
                    content=snapshot_content,
                    filename=f"pre_import_snapshot_{timestamp}.json",
                    content_type="application/json",
                    entity_type="config_snapshot",
                    entity_id=uuid7(),
                    sub_path="snapshots/config",
                    extra={
                        "trigger": "pre_import",
                        "import_filename": data.filename,
                    },
                )
            except Exception:
                logger.exception("Failed to create pre-import snapshot")

        await import_entities(import_data)
