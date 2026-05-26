from __future__ import annotations

import datetime as dt
from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column


class AccountLinkCode(UUIDAuditBase):
    """Short-lived pairing code that links an external identity to a user_account.

    Used wherever we need an out-of-band ("device") flow to bind a remote
    identity (Teams AAD oid, Slack user id, Discord id, …) to one of our
    internal users. The external surface (bot, CLI, …) requests a code; the
    user signs into the admin UI and confirms.

    Schema is provider-agnostic:
      - ``provider`` matches ``user_account_oauth.oauth_name`` (e.g.
        "microsoft", "slack"), so consume() can write the resulting
        OAuth-link row without any provider-specific branching.
      - ``channel_kind`` / ``channel_id`` carry source-channel context — for
        Teams: ``("teams", bot_id)``; for Slack: ``("slack", team_id)``.
        Used to (a) keep concurrent /link sessions on different channels
        independent and (b) pick the right post-consume hook (e.g. Teams
        backfills ``teams_user.tenant_id``).
      - ``extra`` is a free-form JSONB bag for provider-specific snapshot
        data (e.g. user_principal_name, aad_tenant_id) the confirm UI may
        want to render. The core flow never reads it.

    Not tenant-scoped: pre-auth by design (the AAD oid is known before the
    consuming user is). Single-use, 10-minute TTL.
    """

    __tablename__ = "account_link_code"
    __table_args__ = (
        UniqueConstraint("code", name="uq_account_link_code_code"),
        Index(
            "ix_account_link_code_code",
            "code",
            postgresql_where=text("consumed_at IS NULL"),
        ),
        Index(
            "uq_account_link_code_active",
            "provider",
            "subject_id",
            text("COALESCE(channel_id, '')"),
            unique=True,
            postgresql_where=text("consumed_at IS NULL"),
        ),
        Index("ix_account_link_code_expires_at", "expires_at"),
    )

    code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Random pairing code shown to the user on the external surface",
    )

    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="OAuth provider name; matches user_account_oauth.oauth_name",
    )
    subject_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The provider's unique user id (AAD oid, Slack user id, etc.)",
    )

    channel_kind: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="Source channel (e.g. 'teams', 'slack') — drives post-consume hooks",
    )
    channel_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Source-channel id (Teams bot id, Slack team id, …)",
    )

    # Snapshot for the confirm UI.
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra: Mapped[Optional[dict[str, Any]]] = mapped_column(JsonB, nullable=True)

    expires_at: Mapped[dt.datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=False,
    )
    consumed_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
    )
    consumed_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
