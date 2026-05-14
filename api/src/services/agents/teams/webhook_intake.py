"""Intake layer for Microsoft Graph webhook notifications.

Two responsibilities:

1. **Deduplication.** Graph guarantees at-least-once delivery; the same
   notification can land twice. We persist each item to
   ``teams_webhook_event`` under a unique
   ``(subscription_id, resource_id, change_type)`` index. Duplicates are
   silently skipped so the downstream pipeline runs at most once.
2. **Durable staging.** The full notification payload is stored as JSONB
   in the same row so a worker can resume processing even if the API
   process restarts between webhook ack (HTTP 202) and start of work.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-1 and § P0-2.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent
from core.db.session import async_session_maker

logger = getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WebhookIntakeRecord:
    """Result of inserting one webhook notification item."""

    event_id: UUID
    subscription_id: str
    resource_id: str
    change_type: str
    is_duplicate: bool


def _extract_resource_id(notification: dict[str, Any]) -> str | None:
    """Resolve the per-notification resource id.

    For recordings-ready we prefer ``resourceData.id`` (Graph's recording
    object id); we fall back to the ``resource`` URI string when that's
    missing so we still get a stable key.
    """
    data = notification.get("resourceData")
    if isinstance(data, dict):
        rid = data.get("id")
        if isinstance(rid, str) and rid:
            return rid
    resource = notification.get("resource")
    if isinstance(resource, str) and resource:
        return resource
    return None


async def record_webhook_notification(
    *,
    notification: dict[str, Any],
    webhook_kind: str,
    trace_id: str | None = None,
) -> WebhookIntakeRecord | None:
    """Insert (or detect-duplicate) one Graph notification item.

    Returns ``None`` if the notification is missing required identifiers
    (subscription_id / resource id) — that's a client error and the
    caller should reject the webhook upstream.

    Otherwise returns a :class:`WebhookIntakeRecord` with
    ``is_duplicate=True`` when this exact item has been seen before.
    """
    subscription_id = notification.get("subscriptionId")
    if not isinstance(subscription_id, str) or not subscription_id:
        logger.warning("webhook intake: missing subscriptionId, kind=%s", webhook_kind)
        return None

    resource_id = _extract_resource_id(notification)
    if not resource_id:
        logger.warning(
            "webhook intake: missing resource id, sub=%s kind=%s",
            subscription_id,
            webhook_kind,
        )
        return None

    change_type = str(notification.get("changeType") or "unknown")

    async with async_session_maker() as session:
        stmt = (
            pg_insert(TeamsWebhookEvent)
            .values(
                subscription_id=subscription_id,
                resource_id=resource_id,
                change_type=change_type,
                webhook_kind=webhook_kind,
                notification=notification,
                trace_id=trace_id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "subscription_id",
                    "resource_id",
                    "change_type",
                ]
            )
            .returning(TeamsWebhookEvent.id)
        )
        result = await session.execute(stmt)
        new_id = result.scalar_one_or_none()

        if new_id is None:
            # Conflict — the row already exists. Fetch its id for logging.
            from sqlalchemy import select

            existing = await session.execute(
                select(TeamsWebhookEvent.id).where(
                    TeamsWebhookEvent.subscription_id == subscription_id,
                    TeamsWebhookEvent.resource_id == resource_id,
                    TeamsWebhookEvent.change_type == change_type,
                )
            )
            event_id = existing.scalar_one()
            await session.commit()
            logger.info(
                "webhook intake: duplicate ignored sub=%s resource=%s change=%s",
                subscription_id,
                resource_id,
                change_type,
            )
            return WebhookIntakeRecord(
                event_id=event_id,
                subscription_id=subscription_id,
                resource_id=resource_id,
                change_type=change_type,
                is_duplicate=True,
            )

        await session.commit()
        return WebhookIntakeRecord(
            event_id=new_id,
            subscription_id=subscription_id,
            resource_id=resource_id,
            change_type=change_type,
            is_duplicate=False,
        )


async def mark_event_status(
    *,
    event_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    """Update the lifecycle status of a webhook event.

    Used by the worker that processes the notification — flips the row
    from `received` → `enqueued` → `processing` → `done`/`failed`.
    """
    from datetime import datetime, timezone

    from sqlalchemy import update

    async with async_session_maker() as session:
        values: dict[str, Any] = {"status": status}
        if status in {"done", "failed"}:
            values["processed_at"] = datetime.now(timezone.utc)
        if error is not None:
            values["error"] = error[:2000]
        await session.execute(
            update(TeamsWebhookEvent)
            .where(TeamsWebhookEvent.id == event_id)
            .values(**values)
        )
        await session.commit()
