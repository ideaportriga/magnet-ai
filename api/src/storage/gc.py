"""Storage GC job — physically deletes soft-deleted and orphaned tmp files."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from advanced_alchemy.types.file_object import storages
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import StorageConfig
from .models import StoredFile

log = logging.getLogger(__name__)


async def run_storage_gc(
    db_session: AsyncSession,
    cfg: StorageConfig | None = None,
) -> dict[str, int]:
    """Physically delete soft-deleted files and orphaned tmp processing files.

    This function is designed to be called from a scheduler job.

    Returns:
        Dict with ``deleted_files`` and ``freed_bytes`` counts.
    """
    cfg = cfg or StorageConfig()
    now = datetime.now(timezone.utc)

    deleted_files = 0
    freed_bytes = 0
    failed_files = 0

    # 1. Soft-deleted files past retention
    soft_cutoff = now - timedelta(hours=cfg.gc_soft_delete_retention_hours)
    stmt = select(StoredFile).where(
        StoredFile.deleted_at.isnot(None),
        StoredFile.deleted_at < soft_cutoff,
    )
    result = await db_session.execute(stmt)
    expired = list(result.scalars().all())

    purged_ids: list = []
    for sf in expired:
        try:
            backend = storages.get_backend(sf.backend_key)
            await backend.delete_object_async(sf.path)
            purged_ids.append(sf.id)
            deleted_files += 1
            freed_bytes += sf.size
        except Exception:
            log.warning(
                "Failed to delete file from backend %s: %s", sf.backend_key, sf.path
            )
            failed_files += 1

    if purged_ids:
        await db_session.execute(
            delete(StoredFile).where(StoredFile.id.in_(purged_ids))
        )
        await db_session.flush()

    # 2. Orphaned tmp files past retention (tmp_processing + ks_source_temp)
    tmp_cutoff = now - timedelta(hours=cfg.gc_tmp_retention_hours)
    stmt_tmp = select(StoredFile).where(
        StoredFile.entity_type.in_(["tmp_processing", "ks_source_temp"]),
        StoredFile.created_at < tmp_cutoff,
        StoredFile.deleted_at.is_(None),
    )
    result_tmp = await db_session.execute(stmt_tmp)
    orphaned = list(result_tmp.scalars().all())

    purged_tmp_ids: list = []
    for sf in orphaned:
        try:
            backend = storages.get_backend(sf.backend_key)
            await backend.delete_object_async(sf.path)
            purged_tmp_ids.append(sf.id)
            deleted_files += 1
            freed_bytes += sf.size
        except Exception:
            log.warning(
                "Failed to delete tmp file from backend %s: %s",
                sf.backend_key,
                sf.path,
            )
            failed_files += 1

    if purged_tmp_ids:
        await db_session.execute(
            delete(StoredFile).where(StoredFile.id.in_(purged_tmp_ids))
        )
        await db_session.flush()

    if deleted_files or failed_files:
        log.info(
            "Storage GC: deleted %d file(s), freed %d bytes, %d failed",
            deleted_files,
            freed_bytes,
            failed_files,
        )

    return {
        "deleted_files": deleted_files,
        "freed_bytes": freed_bytes,
        "failed_files": failed_files,
    }
