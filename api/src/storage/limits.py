"""File size and quota checks — uses StorageResolver (providers) or env fallback."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar.exceptions import ClientException

from .config import StorageConfig

if TYPE_CHECKING:
    from .resolver import StorageResolver
    from .service import StorageService

    from sqlalchemy.ext.asyncio import AsyncSession


class FileLimits:
    """Validates file size and storage quotas.

    If *resolver* is provided (built from DB providers) it is the primary source
    of truth.  Otherwise the env-based *cfg* is used as fallback.
    """

    def __init__(
        self,
        resolver: StorageResolver | None = None,
        cfg: StorageConfig | None = None,
    ) -> None:
        self._resolver = resolver
        self._cfg = cfg or StorageConfig()

    # --- backend routing ---

    def backend_key_for(self, entity_type: str) -> str:
        if self._resolver:
            return self._resolver.backend_key_for(entity_type)
        return {
            "kg_source": self._cfg.kg_files_backend,
            "kg_upload": self._cfg.kg_files_backend,
            "ks_source": self._cfg.ks_files_backend,
            "recording": self._cfg.recordings_backend,
            "transcription": self._cfg.transcriptions_backend,
        }.get(entity_type, "default")

    # --- limits ---

    def max_file_bytes(self, entity_type: str) -> int:
        if self._resolver:
            return self._resolver.max_file_bytes(entity_type)
        override = {
            "kg_source": self._cfg.kg_max_file_size_mb,
            "kg_upload": self._cfg.kg_max_file_size_mb,
            "ks_source": self._cfg.ks_max_file_size_mb,
        }.get(entity_type, 0)
        mb = override or self._cfg.max_file_size_mb
        return mb * 1024 * 1024 if mb > 0 else 0

    def quota_bytes(self, entity_type: str) -> int:
        if self._resolver:
            return self._resolver.quota_bytes(entity_type)
        mb = {
            "kg_source": self._cfg.kg_source_quota_mb,
            "kg_upload": self._cfg.kg_quota_mb,
            "ks_source": self._cfg.ks_quota_mb,
        }.get(entity_type, 0)
        return mb * 1024 * 1024 if mb > 0 else 0

    # --- checks ---

    def check_file_size(self, size: int, entity_type: str) -> None:
        limit = self.max_file_bytes(entity_type)
        if limit and size > limit:
            raise ClientException(
                detail=f"File exceeds maximum size of {limit // (1024 * 1024)} MB",
            )

    async def check_quota(
        self,
        db_session: AsyncSession,
        storage_service: StorageService,
        entity_type: str,
        entity_id: UUID,
        new_size: int,
    ) -> None:
        quota = self.quota_bytes(entity_type)
        if not quota:
            return
        used = await storage_service.get_used_quota(db_session, entity_type, entity_id)
        if used + new_size > quota:
            available_mb = max((quota - used) // (1024 * 1024), 0)
            raise ClientException(
                detail=f"Storage quota exceeded. Available: {available_mb} MB",
            )
