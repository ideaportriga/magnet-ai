from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.audit.mixin import Auditable

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..provider import Provider
    from ..tenant.tenant import Tenant
    from ..user.user import User


class Collection(UUIDAuditSimpleBase, Auditable):
    __audit_entity_type__ = "collection"
    """Tenant + record-level scoped collection (PR 10 rollout).

    Mirrors the pattern proven in `agents`:
      - `tenant_id` NOT NULL FK + Postgres RLS policy `collections_tenant_isolation`.
      - `system_name` unique **per tenant**, not globally — see partial UNIQUE.
      - `owner_id` / `department_id` / `visibility` for record-level ACL.
    """

    __tablename__ = "collections"
    __table_args__ = (
        Index(
            "uq_collections_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_collections_tenant_id", "tenant_id"),
        Index("ix_collections_owner_id", "owner_id"),
        Index("ix_collections_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_collections_visibility",
        ),
        # Composite FK to providers (tenant_id, system_name) — replaces the
        # legacy single-column FK to providers.system_name.
        ForeignKeyConstraint(
            ["tenant_id", "provider_system_name"],
            ["providers.tenant_id", "providers.system_name"],
            name="fk_collections_provider_tenant_system_name",
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Organization-tenant this collection belongs to (RLS pivot)",
    )

    system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="System name (unique within tenant)",
    )

    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
    )

    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="tenant",
        server_default="tenant",
    )

    tenant: Mapped["Tenant"] = relationship(lazy="noload")
    owner: Mapped[Optional["User"]] = relationship(lazy="noload")
    department: Mapped[Optional["Department"]] = relationship(lazy="noload")

    # Provider system_name — composite FK with tenant_id (see __table_args__).
    provider_system_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider system_name (composite FK with tenant_id)",
        index=True,
    )

    # Relationship to Provider (named provider_rel to avoid potential conflicts)
    provider_rel: Mapped[Optional["Provider"]] = relationship(
        "Provider",
        back_populates="collections",
        foreign_keys=[provider_system_name],
        primaryjoin=(
            "and_(Collection.tenant_id == Provider.tenant_id, "
            "Collection.provider_system_name == Provider.system_name)"
        ),
        lazy="noload",
    )

    # API configuration fields
    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Collection type (e.g., 'documents', 'images')",
    )

    ai_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Model used for processing (e.g., 'AZURE_AI_TEXT-EMBEDDING-3-SMALL')",
    )

    source: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Source configuration for the collection"
    )

    chunking: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Chunking configuration for the collection"
    )

    indexing: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Indexing configuration for the collection"
    )

    metadata_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Metadata configuration for the collection"
    )

    last_synced: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC, nullable=True, comment="Last synced timestamp for the collection"
    )

    job_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Job ID associated with the collection"
    )
