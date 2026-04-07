"""
User account table definition.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC, EncryptedText, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .role import Role
    from .user_oauth_account import UserOAuthAccount
    from .user_role import UserRole


class User(UUIDv7AuditBase):
    """User account for application access.

    Stores local profile data for users authenticated via OIDC (Microsoft/Oracle)
    or API keys. Created automatically on first login (upsert).
    """

    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
        comment="User email address (unique identifier)",
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        comment="Display name",
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
        default=None,
        comment="URL to user avatar image",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="Whether the user account is active",
        index=True,
    )

    is_superuser: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether the user has superuser privileges",
    )

    is_verified: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether the user email has been verified",
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="Timestamp of last successful login",
    )

    # Local auth fields
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
        comment="Argon2 password hash (for local auth)",
    )

    # MFA fields
    is_two_factor_enabled: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether TOTP-based 2FA is enabled",
    )

    totp_secret: Mapped[Optional[str]] = mapped_column(
        EncryptedText,
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
        comment="TOTP secret key (encrypted via SECRET_ENCRYPTION_KEY)",
    )

    backup_codes: Mapped[Optional[list]] = mapped_column(
        JsonB,
        nullable=True,
        default=None,
        comment="Hashed MFA backup codes (Argon2)",
    )

    two_factor_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="When 2FA was confirmed by user",
    )

    # Relationships
    oauth_accounts: Mapped[list[UserOAuthAccount]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    user_roles: Mapped[list[UserRole]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        viewonly=True,
    )

    roles: Mapped[list[Role]] = relationship(
        secondary="user_role",
        lazy="selectin",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<User(email='{self.email}', is_active={self.is_active})>"
