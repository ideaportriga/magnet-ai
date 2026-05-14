"""Webhook intake deduplication tests.

Covers docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-1: the same Graph
notification arriving twice must produce exactly one row, and the second
call must report it as a duplicate (so the webhook handler skips enqueue).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent
from services.agents.teams.webhook_intake import (
    mark_event_status,
    record_webhook_notification,
)


def _notification(*, sub: str, resource_id: str, change: str = "created") -> dict:
    return {
        "subscriptionId": sub,
        "changeType": change,
        "resource": f"communications/onlineMeetings('m1')/recordings('{resource_id}')",
        "resourceData": {
            "id": resource_id,
            "@odata.type": "#Microsoft.Graph.callRecording",
        },
        "clientState": "irrelevant-here-handler-strips-it",
    }


@pytest.mark.asyncio
async def test_first_delivery_inserts_row(db_session):
    intake = await record_webhook_notification(
        notification=_notification(sub="s1", resource_id="r1"),
        webhook_kind="recordings-ready",
    )
    assert intake is not None
    assert intake.is_duplicate is False

    rows = (await db_session.execute(select(TeamsWebhookEvent))).scalars().all()
    assert len(rows) == 1
    assert rows[0].subscription_id == "s1"
    assert rows[0].resource_id == "r1"
    assert rows[0].change_type == "created"
    assert rows[0].webhook_kind == "recordings-ready"
    assert rows[0].status == "received"


@pytest.mark.asyncio
async def test_duplicate_delivery_is_detected(db_session):
    notif = _notification(sub="s2", resource_id="r2")

    first = await record_webhook_notification(
        notification=notif, webhook_kind="recordings-ready"
    )
    second = await record_webhook_notification(
        notification=notif, webhook_kind="recordings-ready"
    )

    assert first is not None and first.is_duplicate is False
    assert second is not None and second.is_duplicate is True
    assert second.event_id == first.event_id

    rows = (await db_session.execute(select(TeamsWebhookEvent))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_distinct_resources_get_distinct_rows(db_session):
    a = await record_webhook_notification(
        notification=_notification(sub="s3", resource_id="r-a"),
        webhook_kind="recordings-ready",
    )
    b = await record_webhook_notification(
        notification=_notification(sub="s3", resource_id="r-b"),
        webhook_kind="recordings-ready",
    )
    assert a is not None and b is not None
    assert a.event_id != b.event_id

    rows = (await db_session.execute(select(TeamsWebhookEvent))).scalars().all()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_missing_subscription_id_returns_none(db_session):
    intake = await record_webhook_notification(
        notification={"resource": "x", "resourceData": {"id": "y"}},
        webhook_kind="recordings-ready",
    )
    assert intake is None


@pytest.mark.asyncio
async def test_missing_resource_id_returns_none(db_session):
    intake = await record_webhook_notification(
        notification={"subscriptionId": "s", "changeType": "created"},
        webhook_kind="recordings-ready",
    )
    assert intake is None


@pytest.mark.asyncio
async def test_mark_event_status_done(db_session):
    intake = await record_webhook_notification(
        notification=_notification(sub="s4", resource_id="r4"),
        webhook_kind="recordings-ready",
    )
    assert intake is not None

    await mark_event_status(event_id=intake.event_id, status="done")

    row = (
        await db_session.execute(
            select(TeamsWebhookEvent).where(TeamsWebhookEvent.id == intake.event_id)
        )
    ).scalar_one()
    assert row.status == "done"
    assert row.processed_at is not None


@pytest.mark.asyncio
async def test_mark_event_status_failed_records_error(db_session):
    intake = await record_webhook_notification(
        notification=_notification(sub="s5", resource_id="r5"),
        webhook_kind="recordings-ready",
    )
    assert intake is not None

    await mark_event_status(event_id=intake.event_id, status="failed", error="boom")

    row = (
        await db_session.execute(
            select(TeamsWebhookEvent).where(TeamsWebhookEvent.id == intake.event_id)
        )
    ).scalar_one()
    assert row.status == "failed"
    assert row.error == "boom"
    assert row.processed_at is not None
