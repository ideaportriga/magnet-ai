from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import Boolean, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column


class TeamsMeeting(BigIntAuditBase):
    """Persistent storage for Teams meeting bot state."""

    __tablename__ = "teams_meeting"
    __table_args__ = (
        Index(
            "ix_teams_meeting_graph_online_meeting_id",
            "graph_online_meeting_id",
        ),
    )

    # Core identities
    chat_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        comment="Teams meeting chat / conversation ID",
    )
    graph_online_meeting_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        unique=True,
        comment="Graph OnlineMeeting ID for recording subscriptions",
    )

    # Optional cache / display
    join_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Meeting join link"
    )
    title: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Meeting subject/title"
    )

    # Bot presence
    is_bot_installed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Whether the bot is currently installed in the meeting",
    )
    removed_from_meeting_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Timestamp when the bot was removed from the meeting",
    )

    # Current recordings subscription (0 or 1 per meeting)
    subscription_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        unique=True,
        comment="Graph subscription ID for recordings",
    )
    subscription_expires_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Cached subscription expiration time",
    )
    subscription_is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Whether the subscription is currently active",
    )
    subscription_last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last error received while managing the subscription",
    )

    # For proactive messaging
    subscription_conversation_reference: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="ConversationReference snapshot for proactive messaging",
    )

    # Bookkeeping
    last_seen_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Last time the bot observed activity in this meeting",
    )
    last_recordings_check_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Last time recordings were checked for this meeting",
    )
    extra: Mapped[dict] = mapped_column(
        JsonB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Additional metadata",
    )
