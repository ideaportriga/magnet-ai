from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config.base import get_general_settings
from core.db.types import EncryptedJsonB

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User


class APIServer(UUIDAuditSimpleBase):
    """Tenant + record-level scoped API server (PR 10 rollout)."""

    __tablename__ = "api_servers"
    __table_args__ = (
        Index(
            "uq_api_servers_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_api_servers_tenant_id", "tenant_id"),
        Index("ix_api_servers_owner_id", "owner_id"),
        Index("ix_api_servers_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_api_servers_visibility",
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

    url: Mapped[str] = mapped_column(String, nullable=False, comment="API server URL")
    custom_headers: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Custom headers configuration"
    )
    security_scheme: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Security scheme configuration"
    )
    security_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Security values configuration"
    )
    verify_ssl: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="SSL verification flag"
    )
    tools: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True, comment="Tools configuration as array of dictionaries"
    )
    secrets_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(
        EncryptedJsonB(key=get_general_settings().SECRET_ENCRYPTION_KEY),
        nullable=True,
        comment="Encrypted secrets configuration",
    )
