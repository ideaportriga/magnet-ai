"""StoredFile — universal file reference tied to any entity."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column


class StoredFile(UUIDv7AuditBase):
    """Universal file reference tied to any entity via polymorphic FK."""

    __tablename__ = "stored_files"
    __table_args__ = (
        Index("ix_stored_files_entity", "entity_type", "entity_id"),
        Index("ix_stored_files_backend_path", "backend_key", "path", unique=True),
        Index("ix_stored_files_tenant_id", "tenant_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        comment=(
            "Organization tenant. Auto-filled by the before_flush listener in "
            "core.db.rls_context from the request context. Enforced by "
            "stored_files_tenant_isolation RLS policy."
        ),
    )

    backend_key: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extra: Mapped[Optional[dict[str, Any]]] = mapped_column(JsonB, nullable=True)
