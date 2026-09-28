"""``price_token_usage`` — the token pricing core."""

from __future__ import annotations

import pytest

from services.ai_services.pricing import (
    _get_model_pricing,
    price_token_usage,
)

_ROW = {
    "price_scheme": "anthropic",
    "price_input": "3",
    "price_output": "15",
    "price_cached": "0.3",
    "price_cache_write": "3.75",
    "price_cache_write_1h": "6",
}


def test_splits_prompt_into_standard_cached_and_written():
    cost = price_token_usage(
        _get_model_pricing(_ROW),
        prompt_tokens=10_000,
        completion_tokens=100,
        cached_tokens=4_000,
        cache_write_tokens=3_000,
        cache_write_1h_tokens=1_000,
    )

    assert cost.standard == pytest.approx(3_000 * 3 / 1e6)
    assert cost.cached == pytest.approx(4_000 * 0.3 / 1e6)
    assert cost.cache_write == pytest.approx((2_000 * 3.75 + 1_000 * 6) / 1e6)
    assert cost.output == pytest.approx(100 * 15 / 1e6)
    assert cost.total == pytest.approx(
        cost.standard + cost.cached + cost.cache_write + cost.output
    )


def test_clamps_inconsistent_counts_to_the_prompt():
    cost = price_token_usage(
        _get_model_pricing(_ROW),
        prompt_tokens=1_000,
        completion_tokens=0,
        cached_tokens=800,
        cache_write_tokens=500,
        cache_write_1h_tokens=900,
    )

    # Only 200 tokens are left to have been written, all of them 1-hour.
    assert cost.standard == 0
    assert cost.cache_write == pytest.approx(200 * 6 / 1e6)
