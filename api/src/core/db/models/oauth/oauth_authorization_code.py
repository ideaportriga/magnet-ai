"""OAuth 2.1 authorization codes — single-use, short-lived.

Issued by Magnet at the end of the user-facing /authorize flow and exchanged at
/token for access + refresh tokens. PKCE binding is enforced by the MCP SDK's
TokenHandler against `code_challenge`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class OAuthAuthorizationCode(UUIDv7AuditBase):
    """Single-use OAuth 2.1 authorization code bound to a client + user + PKCE challenge."""

    __tablename__ = "oauth_authorization_code"
    __table_args__ = {"comment": "Single-use OAuth authorization codes (5-min TTL)"}

    code_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="SHA-256 hash of the issued code (plaintext is never stored)",
    )

    client_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        comment="The oauth_client.client_id this code was issued for",
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user who authenticated to produce this code",
    )

    redirect_uri: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Redirect URI presented at /authorize; must match at /token",
    )

    redirect_uri_provided_explicitly: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether redirect_uri was sent on the /authorize request",
    )

    code_challenge: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="PKCE code_challenge (S256) — verified at /token against the verifier",
    )

    scope: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        default=None,
        comment="Space-separated requested scopes (None for default)",
    )

    resource: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        default=None,
        comment="RFC 8707 resource indicator — the audience the resulting token will carry",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        comment="Hard expiry (default 5 min). After this, /token returns invalid_grant.",
    )

    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        default=None,
        comment="When the code was exchanged. Codes are single-use.",
    )

    def __repr__(self) -> str:
        return (
            f"<OAuthAuthorizationCode(client_id='{self.client_id}', "
            f"user_id={self.user_id}, consumed={self.consumed_at is not None})>"
        )
