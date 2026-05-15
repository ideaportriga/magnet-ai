from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditEntityBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User


class Prompt(UUIDAuditEntityBase):
    """Tenant + record-level scoped prompt template (PR 10 rollout).

    Same pattern as `agents`: tenant isolation via RLS, record-level access
    via owner_id / department_id / visibility, `system_name` unique per tenant.
    """

    __tablename__ = "prompts"
    __table_args__ = (
        Index(
            "uq_prompts_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_prompts_tenant_id", "tenant_id"),
        Index("ix_prompts_owner_id", "owner_id"),
        Index("ix_prompts_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_prompts_visibility",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
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
