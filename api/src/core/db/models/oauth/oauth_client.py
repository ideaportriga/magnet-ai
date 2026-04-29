"""OAuth 2.1 client registration table.

Each row represents an MCP/OAuth client (e.g. Claude.ai, MCP Inspector) that is
permitted to initiate the Authorization Code flow against this server. Rows are
created either by an admin in the Vue admin panel or — if dynamic registration
is enabled later — via an RFC 7591 `/register` endpoint.
"""

from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ARRAY, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class OAuthClient(UUIDv7AuditBase):
    """An OAuth 2.1 client that may request authorization for MCP access."""

    __tablename__ = "oauth_client"
    __table_args__ = {"comment": "OAuth 2.1 clients permitted to use the MCP server"}

    client_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="Public identifier the OAuth client sends in /authorize and /token",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable display name (e.g. 'Claude', 'MCP Inspector')",
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Public clients use PKCE only and have no client_secret",
    )

    client_secret_encrypted: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
        default=None,
        comment="Fernet-encrypted client_secret (set only for confidential clients)",
    )

    redirect_uris: Mapped[list[str]] = mapped_column(
        ARRAY(String(1024)),
        nullable=False,
        comment="Whitelist of exact-match redirect URIs (RFC 8252 loopback wildcards "
        "for http://127.0.0.1 / http://localhost are honored at validation time)",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="If false, /authorize and /token reject this client (soft delete)",
    )

    created_via: Mapped[str] = mapped_column(
        String(16),
        default="admin",
        nullable=False,
        comment="Provenance: 'admin' (manual CRUD) or 'dcr' (dynamic registration)",
    )

    def __repr__(self) -> str:
        return f"<OAuthClient(client_id='{self.client_id}', enabled={self.enabled})>"
