"""Trace-id contextvar tests.

Covers the propagation contract from docs/NOTE_TAKER_RELIABILITY_PLAN.md
§ P1-3: the same correlation id flows from webhook receipt through the
worker, STT polling, stage 1 cards, and stage 2 publishes.
"""

from __future__ import annotations

import asyncio

import pytest

from services.agents.teams.trace_context import (
    add_trace_id_to_event_dict,
    bind_trace_id,
    current_trace_id,
    generate_trace_id,
    get_trace_id,
    set_trace_id,
)


def test_generate_trace_id_is_unique_and_short():
    a = generate_trace_id()
    b = generate_trace_id()
    assert a != b
    assert 16 <= len(a) <= 32


def test_get_returns_none_when_unset():
    # Run in a clean context so we don't see ids leaked from earlier tests.
    async def _check() -> str | None:
        return get_trace_id()

    result = asyncio.run(_check())
    assert result is None


def test_bind_trace_id_isolates_scope():
    outer_token = set_trace_id("outer")
    try:
        with bind_trace_id("inner"):
            assert get_trace_id() == "inner"
        assert get_trace_id() == "outer"
    finally:
        current_trace_id.reset(outer_token)


def test_processor_injects_trace_id():
    with bind_trace_id("abc123"):
        out = add_trace_id_to_event_dict(None, "info", {"message": "hi"})
        assert out["trace_id"] == "abc123"


def test_processor_respects_explicit_trace_id():
    with bind_trace_id("from-ctx"):
        out = add_trace_id_to_event_dict(
            None, "info", {"message": "hi", "trace_id": "from-record"}
        )
        assert out["trace_id"] == "from-record"


def test_processor_skips_when_no_trace_id():
    out = add_trace_id_to_event_dict(None, "info", {"message": "hi"})
    assert "trace_id" not in out


@pytest.mark.asyncio
async def test_contextvar_isolated_across_async_tasks():
    """Each asyncio.Task gets its own copy of the contextvar."""
    set_trace_id("parent")

    async def child(name: str) -> str | None:
        set_trace_id(name)
        await asyncio.sleep(0)
        return get_trace_id()

    a, b = await asyncio.gather(child("a"), child("b"))
    assert {a, b} == {"a", "b"}
    # Parent unaffected.
    assert get_trace_id() == "parent"
