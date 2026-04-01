"""
User OAuth account table definition.

Links external identity provider accounts (Microsoft Entra, Oracle OIDC)
to internal User records.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class UserOAuthAccount(UUIDv7AuditBase):
    """OAuth account linked to an internal user.

    Stores the mapping between an external identity provider account
    (e.g., Microsoft Entra ID oid, Oracle OIDC sub) and the internal User record.
    """

    __tablename__ = "user_account_oauth"
    __table_args__ = (
        UniqueConstraint("oauth_name", "account_id", name="uq_oauth_provider_account"),
        {"comment": "OAuth accounts linked to user accounts"},
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_account",
    )

    oauth_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="OAuth provider name (e.g., 'microsoft', 'oracle')",
    )

    account_id: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        comment="Unique user ID from the OAuth provider (oid/sub)",
    )

    account_email: Mapped[Optional[str]] = mapped_column(
        String(320),
        nullable=True,
        comment="Email address from OAuth provider",
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="Timestamp of last login via this OAuth account",
    )

    # OAuth token storage (for social login providers)
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="OAuth access token (encrypted at app layer for social providers)",
    )

    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="OAuth refresh token (encrypted at app layer for social providers)",
    )

    expires_at: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        default=None,
        comment="Token expiration as Unix timestamp",
    )

    # Relationship
    user: Mapped[User] = relationship(
        back_populates="oauth_accounts",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<UserOAuthAccount(provider='{self.oauth_name}', account_id='{self.account_id}')>"
