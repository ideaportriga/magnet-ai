"""Public Files API — unified access to stored files."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from litestar import Controller, Response, delete, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Redirect, Stream
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from storage import StorageService
from storage.models import StoredFile

logger = logging.getLogger(__name__)

_10_MB = 10 * 1024 * 1024


def _content_disposition(filename: str, inline: bool = True) -> dict[str, str]:
    """Build Content-Disposition header safe for non-ASCII filenames (RFC 5987).

    Args:
        filename: Original filename.
        inline: If True, browser opens the file in a tab (for PDF, images, etc.).
                If False, forces download.
    """
    from urllib.parse import quote

    disposition = "inline" if inline else "attachment"
    ascii_name = filename.encode("ascii", "replace").decode("ascii")
    utf8_name = quote(filename, safe="")
    return {
        "Content-Disposition": (
            f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
        ),
    }


class FilesController(Controller):
    """Unified file access — metadata, download, delete."""

    path = "/files"
    tags = ["files"]

    @get("/", status_code=HTTP_200_OK)
    async def list_files(
        self,
        db_session: AsyncSession,
        entity_type: str | None = Parameter(default=None, query="entity_type"),
        backend_key: str | None = Parameter(default=None, query="backend_key"),
        search: str | None = Parameter(default=None, query="search", max_length=200),
        current_page: int = Parameter(default=1, ge=1, query="currentPage"),
        page_size: int = Parameter(default=50, ge=1, le=200, query="pageSize"),
        order_by: str | None = Parameter(default=None, query="orderBy"),
        sort_order: str = Parameter(default="desc", query="sortOrder"),
    ) -> dict[str, Any]:
        """List stored files with optional filtering and pagination."""
        limit = page_size
        offset = (current_page - 1) * page_size

        conditions = [StoredFile.deleted_at.is_(None)]
        if entity_type:
            conditions.append(StoredFile.entity_type == entity_type)
        if backend_key:
            conditions.append(StoredFile.backend_key == backend_key)
        if search:
            conditions.append(StoredFile.filename.ilike(f"%{search}%"))

        count_stmt = select(func.count(StoredFile.id)).where(*conditions)
        total = int((await db_session.execute(count_stmt)).scalar_one())

        # Sorting
        sortable_columns = {
            "filename": StoredFile.filename,
            "content_type": StoredFile.content_type,
            "size": StoredFile.size,
            "entity_type": StoredFile.entity_type,
            "backend_key": StoredFile.backend_key,
            "created_at": StoredFile.created_at,
        }
        sort_col = sortable_columns.get(order_by, StoredFile.created_at)
        order_clause = sort_col.asc() if sort_order == "asc" else sort_col.desc()

        stmt = (
            select(StoredFile)
            .where(*conditions)
            .order_by(order_clause)
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        files = list(result.scalars().all())

        return {
            "items": [
                {
                    "id": str(f.id),
                    "filename": f.filename,
                    "content_type": f.content_type,
                    "size": f.size,
                    "backend_key": f.backend_key,
                    "entity_type": f.entity_type,
                    "entity_id": str(f.entity_id),
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "expires_at": (
                        f.extra.get("expires_at") if isinstance(f.extra, dict) else None
                    ),
                }
                for f in files
            ],
            "total": total,
        }

    @get("/stats", status_code=HTTP_200_OK)
    async def get_stats(
        self,
        db_session: AsyncSession,
    ) -> dict[str, Any]:
        """Aggregated storage statistics by entity_type and backend_key."""
        base = StoredFile.deleted_at.is_(None)

        # Per entity_type
        et_stmt = (
            select(
                StoredFile.entity_type,
                func.count(StoredFile.id).label("count"),
                func.coalesce(func.sum(StoredFile.size), 0).label("total_size"),
            )
            .where(base)
            .group_by(StoredFile.entity_type)
        )
        et_rows = (await db_session.execute(et_stmt)).all()

        # Per backend_key
        bk_stmt = (
            select(
                StoredFile.backend_key,
                func.count(StoredFile.id).label("count"),
                func.coalesce(func.sum(StoredFile.size), 0).label("total_size"),
            )
            .where(base)
            .group_by(StoredFile.backend_key)
        )
        bk_rows = (await db_session.execute(bk_stmt)).all()

        # Totals
        totals_stmt = select(
            func.count(StoredFile.id),
            func.coalesce(func.sum(StoredFile.size), 0),
        ).where(base)
        total_count, total_size = (await db_session.execute(totals_stmt)).one()

        return {
            "total_files": int(total_count),
            "total_size": int(total_size),
            "by_entity_type": [
                {
                    "entity_type": r.entity_type,
                    "count": r.count,
                    "total_size": int(r.total_size),
                }
                for r in et_rows
            ],
            "by_backend": [
                {
                    "backend_key": r.backend_key,
                    "count": r.count,
                    "total_size": int(r.total_size),
                }
                for r in bk_rows
            ],
        }

    @get("/{file_id:uuid}", status_code=HTTP_200_OK)
    async def get_file_metadata(
        self,
        file_id: UUID,
        storage_service: StorageService,
        db_session: AsyncSession,
    ) -> dict:
        """Return StoredFile metadata."""
        stored = await storage_service.get(db_session, file_id)
        if not stored:
            raise NotFoundException(f"File {file_id} not found")
        return {
            "id": str(stored.id),
            "filename": stored.filename,
            "content_type": stored.content_type,
            "size": stored.size,
            "backend_key": stored.backend_key,
            "entity_type": stored.entity_type,
            "entity_id": str(stored.entity_id),
            "created_at": stored.created_at.isoformat() if stored.created_at else None,
        }

    @get("/{file_id:uuid}/download")
    async def download_file(
        self,
        file_id: UUID,
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> Response:
        """Download a file.

        Cloud backends → 302 redirect to signed URL.
        Local backend  → stream or inline response.
        """
        if not storage_service or not db_session:
            raise NotFoundException("Storage service is not available")

        stored = await storage_service.get(db_session, file_id)
        if not stored:
            raise NotFoundException(f"File {file_id} not found")

        # Cloud backends: redirect to signed URL
        if stored.backend_key != "default":
            url = await storage_service.get_file_url(stored, expires_in_seconds=300)
            return Redirect(path=url)

        headers = _content_disposition(stored.filename)

        # Large local files: chunked streaming via aiofiles
        if stored.size > _10_MB:
            import aiofiles
            from storage.config import StorageConfig

            import os

            cfg = StorageConfig()
            file_path = f"{cfg.local_root}/{stored.path}"

            # Prevent path traversal attacks
            resolved = os.path.abspath(file_path)
            if not resolved.startswith(os.path.abspath(cfg.local_root)):
                raise NotFoundException("Invalid file path")

            async def _stream():  # noqa: ANN202
                async with aiofiles.open(file_path, "rb") as f:
                    while True:
                        chunk = await f.read(_10_MB)
                        if not chunk:
                            break
                        yield chunk

            return Stream(
                iterator=_stream(),
                media_type=stored.content_type,
                headers=headers,
            )

        try:
            content = await storage_service.get_file_content(stored)
        except Exception:
            logger.exception("Failed to read file %s from backend", file_id)
            raise NotFoundException(
                f"File {file_id} content not found on storage backend"
            )

        return Response(
            content=content,
            media_type=stored.content_type,
            headers=headers,
        )

    @post("/temp", status_code=HTTP_201_CREATED)
    async def upload_temp_file(
        self,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Upload a file to temporary storage before a knowledge source is created.

        Returns a ``file_id`` that can be passed in ``uploaded_files`` when
        creating a File-type knowledge source.  Temporary files are stored with
        ``entity_type="ks_source_temp"`` and are eligible for periodic cleanup.
        """
        if not storage_service or not db_session:
            raise ClientException("Storage service is not available")

        filename = data.filename or "upload"
        file_bytes = await data.read()

        if not file_bytes:
            raise ClientException("Empty file")

        safe_filename = os.path.basename(filename)
        ext = os.path.splitext(safe_filename)[1].lower()

        from routes.admin.knowledge_sources import KnowledgeSourceFileUploadController

        if ext not in KnowledgeSourceFileUploadController.ALLOWED_EXTENSIONS:
            raise ClientException(
                f"Unsupported file extension '{ext}'. "
                f"Allowed: {', '.join(sorted(KnowledgeSourceFileUploadController.ALLOWED_EXTENSIONS))}"
            )

        from kreuzberg import detect_mime_type

        from storage.config import StorageConfig
        from storage.mime_validation import validate_upload_mime

        detected_mime = detect_mime_type(file_bytes)
        validate_upload_mime(safe_filename, detected_mime)

        cfg = StorageConfig()
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=cfg.gc_tmp_retention_hours
        )

        stored_file = await storage_service.save_file(
            db_session,
            content=file_bytes,
            filename=safe_filename,
            content_type=detected_mime or "application/octet-stream",
            entity_type="ks_source_temp",
            entity_id=uuid7(),
            extra={"expires_at": expires_at.isoformat()},
        )

        logger.info(
            "Uploaded temp file '%s' → file_id=%s, expires_at=%s",
            safe_filename,
            stored_file.id,
            expires_at,
        )
        return {
            "file_id": str(stored_file.id),
            "filename": stored_file.filename,
            "expires_at": expires_at.isoformat(),
        }

    @delete("/{file_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_file(
        self,
        file_id: UUID,
        storage_service: StorageService,
        db_session: AsyncSession,
    ) -> None:
        """Soft-delete a stored file."""
        stored = await storage_service.get(db_session, file_id)
        if not stored:
            raise NotFoundException(f"File {file_id} not found")
        await storage_service.delete_file(db_session, stored)
