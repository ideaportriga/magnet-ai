from __future__ import annotations

import json
from typing import Any, Optional

from advanced_alchemy.types import EncryptedText, JsonB
from sqlalchemy import TEXT, Boolean, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class EncryptedJsonB(TypeDecorator):
    """Custom type that encrypts JSON data."""

    impl = TEXT
    cache_ok = True

    def __init__(self, key: str, **kwargs):
        self.encrypted_type = EncryptedText(key=key)
        super().__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        """Convert dict to JSON string before encryption."""
        if value is not None:
            if isinstance(value, dict):
                value = json.dumps(value)
            return self.encrypted_type.process_bind_param(value, dialect)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt and parse JSON string back to dict."""
        if value is not None:
            decrypted = self.encrypted_type.process_result_value(value, dialect)
            if decrypted is not None:
                try:
                    return json.loads(decrypted)
                except json.JSONDecodeError:
                    return decrypted
        return value


class APIServer(UUIDAuditSimpleBase):
    """API server table for external API configuration."""

    __tablename__ = "api_servers"

    url: Mapped[str] = mapped_column(String, nullable=False, comment="API server URL")
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
        EncryptedJsonB(key="my-secret-key"),
        nullable=True,
        comment="Encrypted secrets configuration",
    )
