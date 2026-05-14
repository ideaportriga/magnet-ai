"""Lifecycle webhook processing.

Microsoft Graph emits a separate ``lifecycle`` notification stream for
recording subscriptions:

* ``reauthorizationRequired`` — the delegated token used to create the
  subscription is about to expire; the subscription must be renewed
  (PATCH /subscriptions/{id}) before it stops delivering events.
* ``subscriptionRemoved`` — the subscription is gone (revoked, expired,
  or the resource itself was deleted). Nothing will arrive on it again.
* ``missed`` — Graph dropped one or more notifications; we'd need to
  poll for recordings since the last successful delivery to recover the
  state. Not implemented yet — out of scope for P1-6 (see § P2 backlog).

The webhook handler stages these into ``teams_webhook_event`` via the
shared intake layer (P0-1); this module is the worker that drains the
lifecycle backlog. See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-6.
"""

from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from core.db.models.teams import TeamsMeeting
from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent
from core.db.session import async_session_maker

logger = getLogger(__name__)


def _extract_lifecycle_event(notification: dict[str, Any]) -> str:
    """Return the lifecycle event name (``""`` if not present)."""
    event = notification.get("lifecycleEvent")
    if isinstance(event, str):
        return event.strip()
    return ""


async def _clear_subscription_id(subscription_id: str, *, reason: str) -> bool:
    """Detach a (gone) Graph subscription id from any TeamsMeeting row.

    Returns True if a row was updated. The row itself stays — only the
    subscription pointer is wiped so the bot will create a fresh one on
    the next meeting start (or admin command).
    """
    async with async_session_maker() as session:
        stmt = (
            update(TeamsMeeting)
            .where(TeamsMeeting.subscription_id == subscription_id)
            .values(
                subscription_id=None,
                subscription_is_active=False,
                subscription_last_error=reason[:1000],
            )
            .returning(TeamsMeeting.id)
        )
        result = await session.execute(stmt)
        affected = result.scalars().all()
        await session.commit()
    if affected:
        logger.info(
            "[teams lifecycle] cleared subscription %s on %d meeting row(s) (%s)",
            subscription_id,
            len(affected),
            reason,
        )
    return bool(affected)


async def _mark_subscription_reauth_needed(
    subscription_id: str, *, reason: str
) -> bool:
    """Record that a subscription needs reauthorization.

    We don't renew automatically yet (that needs delegated-token flow we
    don't have in worker context) — but we surface it on the meeting row
    so /sign-in handlers can act on it, and so dashboards can alert.
    """
    async with async_session_maker() as session:
        stmt = (
            update(TeamsMeeting)
            .where(TeamsMeeting.subscription_id == subscription_id)
            .values(
                subscription_is_active=False,
                subscription_last_error=reason[:1000],
            )
            .returning(TeamsMeeting.id)
        )
        result = await session.execute(stmt)
        affected = result.scalars().all()
        await session.commit()
    if affected:
        logger.warning(
            "[teams lifecycle] subscription %s needs reauthorization (%s); affected meetings=%d",
            subscription_id,
            reason,
            len(affected),
        )
    return bool(affected)


async def process_lifecycle_event(event_id: UUID) -> None:
    """Process one staged lifecycle event row.

    Idempotent: rows already marked ``done`` are skipped; the worker only
    updates ``teams_webhook_event.status`` after the side effect lands.
    """
    async with async_session_maker() as session:
        event = (
            await session.execute(
                select(TeamsWebhookEvent).where(TeamsWebhookEvent.id == event_id)
            )
        ).scalar_one_or_none()
        if event is None:
            logger.warning("lifecycle worker: event %s not found", event_id)
            return
        if event.status == "done":
            logger.info("lifecycle worker: event %s already done, skipping", event_id)
            return
        if event.webhook_kind != "recordings-lifecycle":
            logger.warning(
                "lifecycle worker: event %s is kind=%s, expected recordings-lifecycle",
                event_id,
                event.webhook_kind,
            )
            return
        notification = dict(event.notification or {})
        subscription_id = event.subscription_id

        await session.execute(
            update(TeamsWebhookEvent)
            .where(TeamsWebhookEvent.id == event.id)
            .values(status="processing")
        )
        await session.commit()

    lifecycle_event = _extract_lifecycle_event(notification)
    error_message: str | None = None

    try:
        if lifecycle_event == "subscriptionRemoved":
            await _clear_subscription_id(
                subscription_id, reason="lifecycle: subscriptionRemoved"
            )
        elif lifecycle_event == "reauthorizationRequired":
            await _mark_subscription_reauth_needed(
                subscription_id,
                reason="lifecycle: reauthorizationRequired",
            )
        elif lifecycle_event == "missed":
            # We don't replay missed recordings yet. Log loudly so the
            # alert dashboards can flag it for manual triage.
            logger.warning(
                "[teams lifecycle] 'missed' event for subscription %s — manual replay required",
                subscription_id,
            )
        else:
            logger.info(
                "[teams lifecycle] unhandled lifecycle event %r for subscription %s",
                lifecycle_event or "<missing>",
                subscription_id,
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "[teams lifecycle] processing failed for event %s (sub=%s, kind=%s)",
            event_id,
            subscription_id,
            lifecycle_event,
        )
        error_message = f"{type(exc).__name__}: {exc}"[:2000]

    async with async_session_maker() as session:
        await session.execute(
            update(TeamsWebhookEvent)
            .where(TeamsWebhookEvent.id == event_id)
            .values(
                status="failed" if error_message else "done",
                error=error_message,
                processed_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
