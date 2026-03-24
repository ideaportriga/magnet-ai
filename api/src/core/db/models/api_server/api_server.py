from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from core.config.base import get_general_settings
from core.db.types import EncryptedJsonB

from ..base import UUIDAuditSimpleBase


class APIServer(UUIDAuditSimpleBase):
    """API server table for external API configuration."""

    __tablename__ = "api_servers"

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
