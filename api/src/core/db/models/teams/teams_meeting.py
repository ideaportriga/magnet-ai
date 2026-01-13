from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import Boolean, Index, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column


class TeamsMeeting(BigIntAuditBase):
    """Persistent storage for Teams meeting bot state."""

    __tablename__ = "teams_meeting"
    __table_args__ = (
        Index(
            "ix_teams_meeting_graph_online_meeting_id",
            "graph_online_meeting_id",
        ),
        UniqueConstraint(
            "chat_id",
            "bot_id",
            name="uq_teams_meeting_chat_id_bot_id",
        ),
        UniqueConstraint(
            "graph_online_meeting_id",
            "bot_id",
            name="uq_teams_meeting_graph_online_meeting_id_bot_id",
        ),
    )

    # Core identities
    chat_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Teams meeting chat / conversation ID",
    )
    meeting_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Teams meeting id from channel data",
    )
    graph_online_meeting_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Graph OnlineMeeting ID for recording subscriptions",
    )

    # Optional cache / display
    account_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Salesforce account id linked to this meeting",
    )
    account_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Salesforce account name linked to this meeting",
    )
    bot_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Bot app id installed in meeting",
    )
    note_taker_settings_system_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Note taker settings system name associated with this meeting",
    )

    added_by_user_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Teams user id of the user who added the bot",
    )
    added_by_aad_object_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AAD object id of the user who added the bot",
    )
    added_by_display_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Display name of the user who added the bot",
    )

    # Bot presence
    is_bot_installed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Whether the bot is currently installed in the meeting",
    )
    added_to_meeting_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Timestamp when the bot was added to the meeting",
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
    extra: Mapped[dict] = mapped_column(
        JsonB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Additional metadata",
    )
