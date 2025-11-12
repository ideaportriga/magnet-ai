from __future__ import annotations

from datetime import datetime

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class SlackOAuthState(UUIDAuditBase):
    """Short-lived store for Slack OAuth state tokens."""

    __tablename__ = "slack_oauth_states"
    __table_args__ = (
        UniqueConstraint("state_token", name="uq_slack_oauth_states_state"),
        Index("ix_slack_oauth_states_agent", "agent_system_name"),
        Index("ix_slack_oauth_states_expires_at", "expires_at"),
    )

    state_token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Slack OAuth state token",
    )
    agent_system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Associated agent system name",
    )
    agent_display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Human readable agent name",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=False,
        comment="Expiration timestamp for the state token",
    )
