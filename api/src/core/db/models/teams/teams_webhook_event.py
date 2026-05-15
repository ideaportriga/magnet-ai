"""TeamsWebhookEvent — durable receipts for Microsoft Graph webhook calls.

Microsoft Graph guarantees at-least-once delivery: the same recording-ready
notification can land twice (network retry, ack timeout, redelivery after a
partial outage). Without deduplication the bot would download the recording
twice, submit two STT jobs, and produce duplicate Confluence/Salesforce/KG
posts.

This table records each ``(subscription_id, resource_id, change_type)`` we
have ever accepted. The unique constraint plus
``INSERT ... ON CONFLICT DO NOTHING`` gives us idempotency at the database
boundary — duplicates are visible in `status='duplicate'` (kept around for
audit) and the actual pipeline runs at most once.

Rows are cheap (the original payload is kept as JSONB so the worker can pick
up the work even if the API process restarts before it does) and a
housekeeping cron sweeps anything older than `RETENTION_DAYS`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from advanced_alchemy.types import JsonB
from sqlalchemy import DateTime, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column


class TeamsWebhookEvent(CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs):
    """Durable receipt for a Microsoft Graph webhook notification."""

    __tablename__ = "teams_webhook_event"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "resource_id",
            "change_type",
            name="uq_teams_webhook_event_subscription_resource_change",
        ),
        Index("ix_teams_webhook_event_received_at", "received_at"),
        Index("ix_teams_webhook_event_status", "status"),
        Index("ix_teams_webhook_event_trace_id", "trace_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    subscription_id: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)

    webhook_kind: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="recordings-ready | recordings-lifecycle",
    )

    # Snapshot the original notification item so a worker can pick it up
    # later — survives API process restarts between webhook ack and
    # transcription start.
    notification: Mapped[dict[str, Any]] = mapped_column(JsonB, nullable=False)

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'received'"),
        comment="received | enqueued | processing | done | failed",
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Correlation id propagated from webhook receipt through STT, post-
    # processing, and integration publishes — see
    # docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.
    # Index declared in __table_args__ above (ix_teams_webhook_event_trace_id);
    # do not duplicate via index=True or metadata.create_all double-creates it.
    trace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Retry counter for transient failures during download / Graph API.
    # See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-4.
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
