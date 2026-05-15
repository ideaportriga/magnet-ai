from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditEntityBase

if TYPE_CHECKING:
    from core.db.models.department.department import Department
    from core.db.models.tenant.tenant import Tenant
    from core.db.models.user.user import User


class Agent(UUIDAuditEntityBase):
    """Tenant + record-level scoped agent table.

    Tenant scope (PR 7):
      - `tenant_id` NOT NULL FK to `tenant`.
      - `system_name` is unique **per tenant**, not globally.
      - Postgres RLS policy `agents_tenant_isolation` enforces tenant isolation.

    Record-level access (PR 8):
      - `owner_id` — user who created/owns the row (NULL for legacy rows).
      - `department_id` — optional org-unit; used when `visibility='department'`.
      - `visibility` — one of `'private' | 'department' | 'tenant'`; gates
        which users (beyond owner / admin / explicit grants) can view the row.
    """

    __tablename__ = "agents"
    __table_args__ = (
        Index(
            "uq_agents_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_agents_tenant_id", "tenant_id"),
        Index("ix_agents_owner_id", "owner_id"),
        Index("ix_agents_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_agents_visibility",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Organization-tenant this agent belongs to (RLS pivot)",
    )

    # Override the base column to drop the global `unique=True`. The
    # tenant-scoped partial unique above replaces it.
    system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="System name (unique within tenant; see partial UNIQUE)",
    )

    channels: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="List of agent channels"
    )

    # ── Record-level fields (PR 8) ───────────────────────────────────────

    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Owner user (the creator). NULL after owner is deleted.",
    )

    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
        comment="Department this agent belongs to (for visibility='department')",
    )

    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="tenant",
        server_default="tenant",
        comment="'private' | 'department' | 'tenant'",
    )

    # ── Relationships (lazy=noload to avoid surprises) ────────────────────

    tenant: Mapped[Tenant] = relationship(lazy="noload")
    owner: Mapped[Optional[User]] = relationship(lazy="noload")
    department: Mapped[Optional[Department]] = relationship(lazy="noload")
