"""StorageService — CRUD for stored files, quota management, backend I/O."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any, Union
from uuid import UUID

from advanced_alchemy.types.file_object import storages
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from .models import StoredFile

log = logging.getLogger(__name__)


class StorageService:
    """Coordinates file I/O on backends with StoredFile metadata in the DB."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def save_file(
        self,
        db_session: AsyncSession,
        *,
        content: Union[bytes, AsyncIterator[bytes]],
        filename: str,
        content_type: str,
        entity_type: str,
        entity_id: UUID,
        size: int | None = None,
        backend_key: str = "default",
        sub_path: str = "",
        extra: dict[str, Any] | None = None,
    ) -> StoredFile:
        """Save a file to the backend and create a StoredFile record.

        Args:
            content: Raw bytes or an async iterator of chunks.
            size: Required when *content* is an async iterator (for quota checks).
        """
        if isinstance(content, bytes):
            data: bytes = content
            file_size = len(data)
        else:
            data = await _drain_async_iterator(content)
            file_size = len(data)

        if size is not None:
            file_size = size

        # Build storage path
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = (
            f"{sub_path}/{uuid7()}-{safe_name}"
            if sub_path
            else f"{uuid7()}-{safe_name}"
        )
        path = path.lstrip("/")

        # Write to backend
        backend = storages.get_backend(backend_key)
        await backend.fs.put_async(path, data)

        # Persist metadata
        stored = StoredFile(
            backend_key=backend_key,
            path=path,
            filename=filename,
            content_type=content_type,
            size=file_size,
            entity_type=entity_type,
            entity_id=entity_id,
            extra=extra,
        )
        db_session.add(stored)
        await db_session.flush()

        log.info(
            "Saved file '%s' (%d bytes) to backend '%s' path '%s'",
            filename,
            file_size,
            backend_key,
            path,
        )
        return stored

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, db_session: AsyncSession, file_id: UUID) -> StoredFile | None:
        stmt = select(StoredFile).where(
            StoredFile.id == file_id,
            StoredFile.deleted_at.is_(None),
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entity_files(
        self,
        db_session: AsyncSession,
        entity_type: str,
        entity_id: UUID,
    ) -> list[StoredFile]:
        stmt = select(StoredFile).where(
            StoredFile.entity_type == entity_type,
            StoredFile.entity_id == entity_id,
            StoredFile.deleted_at.is_(None),
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_file_content(self, stored_file: StoredFile) -> bytes:
        backend = storages.get_backend(stored_file.backend_key)
        return await backend.get_content_async(stored_file.path)

    async def get_file_url(
        self,
        stored_file: StoredFile,
        *,
        expires_in_seconds: int = 3600,
        base_api_url: str = "/api/files",
    ) -> str:
        """Return a download URL.

        Cloud backends → signed URL.
        Local backend  → API endpoint path.
        """
        if stored_file.backend_key == "default":
            return f"{base_api_url}/{stored_file.id}/download"

        backend = storages.get_backend(stored_file.backend_key)
        try:
            url = await backend.sign_async(
                stored_file.path,
                expires_in=expires_in_seconds,
            )
            return url  # type: ignore[return-value]
        except (NotImplementedError, ValueError):
            return f"{base_api_url}/{stored_file.id}/download"

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_file(
        self,
        db_session: AsyncSession,
        stored_file: StoredFile,
    ) -> None:
        """Soft-delete a stored file (physical removal via GC job)."""
        stored_file.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()

    async def delete_entity_files(
        self,
        db_session: AsyncSession,
        entity_type: str,
        entity_id: UUID,
    ) -> None:
        """Soft-delete all files belonging to an entity."""
        files = await self.get_entity_files(db_session, entity_type, entity_id)
        now = datetime.now(timezone.utc)
        for f in files:
            f.deleted_at = now
        await db_session.flush()

    # ------------------------------------------------------------------
    # Quota
    # ------------------------------------------------------------------

    async def get_used_quota(
        self,
        db_session: AsyncSession,
        entity_type: str,
        entity_id: UUID,
    ) -> int:
        """Return total bytes used by an entity."""
        stmt = select(func.coalesce(func.sum(StoredFile.size), 0)).where(
            StoredFile.entity_type == entity_type,
            StoredFile.entity_id == entity_id,
            StoredFile.deleted_at.is_(None),
        )
        result = await db_session.execute(stmt)
        return int(result.scalar_one())

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    async def copy_file(
        self,
        db_session: AsyncSession,
        stored_file: StoredFile,
        *,
        target_backend_key: str,
        target_entity_type: str | None = None,
        target_entity_id: UUID | None = None,
    ) -> StoredFile:
        """Copy a file to another backend."""
        content = await self.get_file_content(stored_file)
        return await self.save_file(
            db_session,
            content=content,
            filename=stored_file.filename,
            content_type=stored_file.content_type,
            entity_type=target_entity_type or stored_file.entity_type,
            entity_id=target_entity_id or stored_file.entity_id,
            backend_key=target_backend_key,
            extra=stored_file.extra,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _drain_async_iterator(it: AsyncIterator[bytes]) -> bytes:
    chunks: list[bytes] = []
    async for chunk in it:
        if chunk:
            chunks.append(chunk)
    return b"".join(chunks)
