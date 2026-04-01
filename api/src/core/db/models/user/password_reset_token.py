"""
Password reset token table definition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class PasswordResetToken(UUIDv7AuditBase):
    """One-time token for password reset flow."""

    __tablename__ = "password_reset_token"
    __table_args__ = {"comment": "One-time tokens for password reset"}

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="SHA-256 hash of the reset token",
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_account",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        comment="Token expiration (1 hour from creation)",
    )

    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="When the token was consumed (NULL = unused)",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        default=None,
        comment="IP address that requested the reset",
    )

    def __repr__(self) -> str:
        return f"<PasswordResetToken(user_id='{self.user_id}', used={self.used_at is not None})>"
