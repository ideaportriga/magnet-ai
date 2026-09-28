"""``collect_llm_usage`` sums the usage/cost of v1 LLM calls in a block."""

from __future__ import annotations

import asyncio

import pytest

# Prime config before importing the v1 observability package to avoid the
# circular import (same preamble as ``test_observability_cost_details``).
import core.config.app  # noqa: F401  isort:skip
from services.observability.models import (  # noqa: E402
    CostDetails,
    UsageDetails,
    UsageInputDetails,
)
from services.observability.usage_collector import (  # noqa: E402
    collect_llm_usage,
    record_llm_usage,
)


def _call(prompt: int, completion: int, cached: int | None, cost: float | None):
    return (
        UsageDetails(
            input=prompt,
            output=completion,
            input_details=UsageInputDetails(cached=cached),
        ),
        CostDetails(total=cost),
    )


def test_sums_calls_and_nests():
    with collect_llm_usage() as outer:
        record_llm_usage(*_call(100, 10, 60, 0.5))
        with collect_llm_usage() as inner:
            record_llm_usage(*_call(50, 5, None, 0.25))
        record_llm_usage(None, None)

    assert (inner.prompt_tokens, inner.cost) == (50, 0.25)
    assert (outer.prompt_tokens, outer.completion_tokens, outer.cached_tokens) == (
        150,
        15,
        60,
    )
    assert outer.cost == pytest.approx(0.75)


def test_cost_stays_none_when_no_call_is_priced():
    with collect_llm_usage() as collected:
        record_llm_usage(*_call(100, 10, 0, None))

    assert collected.prompt_tokens == 100
    assert collected.cost is None


def test_no_op_outside_a_collector():
    record_llm_usage(*_call(100, 10, 0, 1.0))  # must not raise


@pytest.mark.anyio
async def test_sees_calls_from_child_tasks():
    async def _llm_call():
        record_llm_usage(*_call(10, 1, 0, 0.1))

    with collect_llm_usage() as collected:
        await asyncio.gather(_llm_call(), _llm_call())

    assert collected.prompt_tokens == 20
    assert collected.cost == pytest.approx(0.2)
