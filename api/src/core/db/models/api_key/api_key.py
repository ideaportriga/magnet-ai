"""
API Keys table definition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import UniqueMixin
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class APIKey(UUIDv7AuditBase, UniqueMixin):
    """
    API Key entity for storing API key configurations and metadata.

    Based on the API key JSON structure with hash and masked value info.
    """

    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="API key name", index=True
    )

    # Key identification and security
    hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of the API key",
        index=True,
        unique=True,
    )

    value_masked: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Masked version of the API key (e.g., '...Gpys')",
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        comment="Expiration date/time",
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="Whether the API key is active",
        index=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the API key",
    )

    def __repr__(self) -> str:
        return f"<APIKey(value_masked='{self.value_masked}')>"
