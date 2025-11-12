from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Boolean, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.config.base import get_general_settings
from core.db.types import EncryptedJsonB

_ENCRYPTION_KEY = get_general_settings().SECRET_ENCRYPTION_KEY


class SlackInstallation(UUIDAuditBase):
    """Persistent storage for Slack OAuth installations."""

    __tablename__ = "slack_installations"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "enterprise_id",
            "team_id",
            "user_id",
            name="uq_slack_installations_scope",
        ),
        Index("ix_slack_installations_agent", "agent_system_name"),
        Index(
            "ix_slack_installations_client_scope",
            "client_id",
            "enterprise_id",
            "team_id",
        ),
        Index("ix_slack_installations_user", "user_id"),
    )

    agent_system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Associated agent system name",
    )
    client_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Slack app client ID",
    )
    app_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Slack app ID",
    )
    enterprise_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Slack enterprise ID when installed for an org",
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Slack workspace/team ID",
    )
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Installer Slack user ID",
    )
    is_enterprise_install: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether the installation covers the entire enterprise",
    )
    installed_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the installation was completed",
    )
    installation_data: Mapped[dict[str, Any]] = mapped_column(
        EncryptedJsonB(key=_ENCRYPTION_KEY),
        nullable=False,
        comment="Full installation payload (encrypted)",
    )
    bot_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        EncryptedJsonB(key=_ENCRYPTION_KEY),
        nullable=True,
        comment="Bot token payload (encrypted)",
    )
