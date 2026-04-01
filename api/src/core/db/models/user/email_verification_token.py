"""
Email verification token table definition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class EmailVerificationToken(UUIDv7AuditBase):
    """One-time token for email verification."""

    __tablename__ = "email_verification_token"
    __table_args__ = {"comment": "One-time tokens for email verification"}

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="SHA-256 hash of the verification token",
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        comment="Email being verified",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        comment="Token expiration (24 hours from creation)",
    )

    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="When the token was consumed (NULL = unused)",
    )

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(email='{self.email}', used={self.used_at is not None})>"
