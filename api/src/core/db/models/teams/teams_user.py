from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column


class TeamsUser(UUIDAuditBase):
    """Teams user info used for proactive messaging."""

    __tablename__ = "teams_user"
    __table_args__ = (
        Index(
            "ix_teams_user_aad_scope",
            "aad_object_id",
            "scope",
            "bot_id",
            unique=True,
            postgresql_where=text("aad_object_id IS NOT NULL"),
        ),
        Index(
            "ix_teams_user_teams_scope",
            "teams_user_id",
            "scope",
            "bot_id",
            unique=True,
        ),
    )

    aad_object_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AAD object id from activity.from.aad_object_id",
    )
    teams_user_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Teams user id from activity.from.id",
    )
    user_principal_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User principal name from roster lookup",
    )
    email: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Email from roster lookup (may be null)",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Display name from the activity",
    )
    scope: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Teams scope: "personal" | "groupChat" | "channel"',
    )
    conversation_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Conversation id for proactive messages",
    )
    service_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Channel service URL",
    )
    bot_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Bot's Teams id (activity.recipient.id)",
    )
    conversation_reference: Mapped[dict[str, Any]] = mapped_column(
        JsonB,
        nullable=False,
        comment="Serialized conversation reference snapshot",
    )
    last_seen_at: Mapped[dt.datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="Updated on every message/install event",
    )
