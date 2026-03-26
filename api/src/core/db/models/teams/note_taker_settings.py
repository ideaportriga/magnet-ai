from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import UUIDAuditSimpleBase


class NoteTakerSettings(UUIDAuditSimpleBase):
    __tablename__ = "note_taker_settings"

    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Settings in JSON format",
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
