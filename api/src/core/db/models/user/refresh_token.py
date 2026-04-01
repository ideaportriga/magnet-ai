"""
Refresh token table definition.

Uses family-based reuse detection: all tokens from the same login session
share a family_id. If a revoked token is presented, the entire family is
revoked to prevent token theft.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class RefreshToken(UUIDv7AuditBase):
    """Refresh token for JWT-based session management."""

    __tablename__ = "refresh_token"
    __table_args__ = {"comment": "Refresh tokens for JWT session management"}

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="SHA-256 hash of the refresh token (never store plaintext)",
    )

    family_id: Mapped[UUID] = mapped_column(
        index=True,
        nullable=False,
        comment="Token family ID — all tokens from one login share this",
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_account",
    )

    device_info: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        default=None,
        comment="User-Agent or device description",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        comment="Token expiration timestamp",
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="When the token was revoked (NULL = active)",
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(family_id='{self.family_id}', revoked={self.revoked_at is not None})>"
