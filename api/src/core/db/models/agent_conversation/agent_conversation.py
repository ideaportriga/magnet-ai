from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class AgentConversation(UUIDv7AuditBase):
    """Main AI app table using base entity class with variant validation."""

    __tablename__ = "agent_conversations"

    # Agent identifier
    agent: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Agent identifier"
    )

    # Timestamp of last user message
    last_user_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC(timezone=True),
        nullable=True,
        comment="Timestamp of last user message",
    )

    # Client identifier
    client_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Client identifier"
    )

    # Trace identifier for request tracking
    trace_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Trace identifier for request tracking"
    )

    # Analytics identifier
    analytics_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Analytics identifier"
    )

    # Variables as JSONB (can store any key-value pairs)
    variables: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Variables in JSON format"
    )

    # Messages as JSONB (nested structure)
    messages: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="List of messages in JSON format"
    )

    # Conversation status
    status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Conversation status"
    )

    # Message processing status
    message_processing_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Message processing status: 'processing', 'completed', or 'failed'",
    )
