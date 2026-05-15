from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.models.base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User


class NoteTakerSettings(UUIDAuditSimpleBase):
    """Tenant + record-level scoped note-taker settings (PR 10 rollout)."""

    __tablename__ = "note_taker_settings"
    __table_args__ = (
        Index(
            "uq_note_taker_settings_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_note_taker_settings_tenant_id", "tenant_id"),
        Index("ix_note_taker_settings_owner_id", "owner_id"),
        Index("ix_note_taker_settings_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_note_taker_settings_visibility",
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

    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Settings in JSON format",
    )

    # Bumped whenever `NoteTakerSettingsSchema` changes shape; used by future
    # migrations that need to rewrite JSONB `config` rows in-place.
    settings_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
        comment="Schema revision for the `config` JSONB payload.",
    )

    # Reference to a Provider record that holds Azure Bot credentials
    # (client_id, client_secret, tenant_id stored in Provider.secrets_encrypted).
    provider_system_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("providers.system_name", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to Provider with Azure Bot credentials for this note-taker.",
    )

    # AAD object-id of the designated superuser for this note-taker.
    # When set, this user can access ALL transcriptions created by this bot,
    # regardless of who initiated them.
    superuser_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AAD object-id of the note-taker superuser (can access all recordings).",
    )
