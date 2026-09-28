"""Model-card cost calculation for v1 LLM calls (``get_usage_and_cost_details``).

Pins the prompt-cache split and the pricing scheme:

- cache reads bill at ``price_cached``;
- ``basic`` (default) bills cache writes at the input price;
- ``openai`` bills them at ``price_cache_write``;
- ``anthropic`` bills 5-minute writes at ``price_cache_write`` and 1-hour writes
  at ``price_cache_write_1h``;
- OpenAI's ``cache_write_tokens`` counts as a cache write like Anthropic's
  ``cache_creation_tokens``;
- unset prices fall back to the input price, and neither reads nor writes are
  double-billed as standard input.
"""

from __future__ import annotations

import pytest

# Prime config before importing the observability package to avoid the
# circular import.
import core.config.app  # noqa: F401  isort:skip
from litellm.types.utils import (  # noqa: E402
    CacheCreationTokenDetails,
    PromptTokensDetailsWrapper,
    Usage,
)

from services.ai_services.models import ModelUsage  # noqa: E402
from services.observability import utils as obs_utils  # noqa: E402

# Prices per 1M tokens, Anthropic-style ratios.
_PRICING = {
    "price_input": "3",
    "price_output": "15",
    "price_cached": "0.3",
    "price_cache_write": "3.75",
    "price_cache_write_1h": "6",
    "price_standard_input_unit_count": 1_000_000,
    "price_cached_input_unit_count": 1_000_000,
    "price_standard_output_unit_count": 1_000_000,
}

_LONG_CONTEXT = {
    "price_long_context_threshold": 200_000,
    "price_long_context_input": "6",
    "price_long_context_cached": "0.6",
    "price_long_context_output": "22.5",
}


def _usage(
    prompt: int,
    completion: int,
    cached: int,
    cache_write: int,
    cache_write_1h: int | None = None,
) -> Usage:
    details = None
    if cache_write_1h is not None:
        details = PromptTokensDetailsWrapper(
            cached_tokens=cached,
            cache_creation_tokens=cache_write,
            cache_creation_token_details=CacheCreationTokenDetails(
                ephemeral_5m_input_tokens=cache_write - cache_write_1h,
                ephemeral_1h_input_tokens=cache_write_1h,
            ),
        )
    return Usage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
        cache_read_input_tokens=cached,
        cache_creation_input_tokens=cache_write,
        prompt_tokens_details=details,
    )


@pytest.fixture
def model_config(monkeypatch):
    config: dict = {}

    async def _get_model(_system_name):
        return config

    monkeypatch.setattr(obs_utils, "get_model_by_system_name", _get_model)
    return config


async def _cost(usage):
    return await obs_utils.get_usage_and_cost_details(usage, "MODEL")


@pytest.mark.anyio
@pytest.mark.parametrize("scheme", [None, "basic"])
async def test_basic_scheme_bills_cache_writes_at_input_price(model_config, scheme):
    model_config.update({**_PRICING, "price_scheme": scheme})

    usage, cost = await _cost(
        _usage(prompt=10_000, completion=1_000, cached=4_000, cache_write=2_000)
    )

    assert usage.input == 10_000
    assert usage.input_details.cached == 4_000
    assert usage.input_details.cache_write == 2_000
    assert usage.input_details.standard == 4_000
    # Configured cache write prices are ignored outside openai/anthropic.
    assert cost.input_details.cache_write == pytest.approx(2_000 * 3 / 1e6)
    assert cost.input_details.cached == pytest.approx(4_000 * 0.3 / 1e6)
    assert cost.input == pytest.approx((6_000 * 3 + 4_000 * 0.3) / 1e6)
    assert cost.total == pytest.approx(cost.input + 1_000 * 15 / 1e6)


@pytest.mark.anyio
async def test_openai_scheme_bills_cache_writes_at_cache_write_price(model_config):
    model_config.update({**_PRICING, "price_scheme": "openai"})

    _, cost = await _cost(
        _usage(
            prompt=10_000,
            completion=0,
            cached=4_000,
            cache_write=2_000,
            cache_write_1h=500,
        )
    )

    # A single cache write price: the 1-hour share is not priced separately.
    assert cost.input_details.cache_write == pytest.approx(2_000 * 3.75 / 1e6)
    assert cost.input_details.standard == pytest.approx(4_000 * 3 / 1e6)


@pytest.mark.anyio
async def test_openai_cache_write_tokens_are_detected(model_config):
    # OpenAI/Azure (GPT-5.6+) report writes as ``cache_write_tokens``, which
    # litellm passes through untouched.
    model_config.update(
        {
            **_PRICING,
            "price_scheme": "openai",
            "price_input": "4",
            "price_cached": "0.4",
            "price_cache_write": "10",
            "price_output": "20",
        }
    )
    usage = Usage(
        prompt_tokens=6724,
        completion_tokens=299,
        total_tokens=7023,
        prompt_tokens_details={"cached_tokens": 6698, "cache_write_tokens": 23},
    )

    usage_details, cost = await _cost(usage)

    assert usage_details.input_details.cache_write == 23
    assert usage_details.input_details.standard == 3
    assert cost.input_details.cache_write == pytest.approx(23 * 10 / 1e6)
    assert cost.total == pytest.approx((3 * 4 + 6698 * 0.4 + 23 * 10 + 299 * 20) / 1e6)


@pytest.mark.anyio
async def test_openai_scheme_falls_back_to_input_price_when_unset(model_config):
    model_config.update(
        {**_PRICING, "price_scheme": "openai", "price_cache_write": None}
    )

    _, cost = await _cost(
        _usage(prompt=10_000, completion=0, cached=0, cache_write=2_000)
    )

    assert cost.input_details.cache_write == pytest.approx(2_000 * 3 / 1e6)
    assert cost.input == pytest.approx(10_000 * 3 / 1e6)


@pytest.mark.anyio
async def test_anthropic_scheme_prices_5m_and_1h_writes_separately(model_config):
    model_config.update({**_PRICING, "price_scheme": "anthropic"})

    usage, cost = await _cost(
        _usage(
            prompt=10_000,
            completion=0,
            cached=0,
            cache_write=3_000,
            cache_write_1h=1_000,
        )
    )

    assert usage.input_details.cache_write == 3_000
    assert usage.input_details.standard == 7_000
    assert cost.input_details.cache_write == pytest.approx(
        (2_000 * 3.75 + 1_000 * 6) / 1e6
    )


@pytest.mark.anyio
async def test_anthropic_scheme_without_1h_split_bills_all_as_5m(model_config):
    model_config.update({**_PRICING, "price_scheme": "anthropic"})

    _, cost = await _cost(
        _usage(prompt=10_000, completion=0, cached=0, cache_write=2_000)
    )

    assert cost.input_details.cache_write == pytest.approx(2_000 * 3.75 / 1e6)


@pytest.mark.anyio
async def test_anthropic_1h_writes_fall_back_to_input_price(model_config):
    model_config.update(
        {**_PRICING, "price_scheme": "anthropic", "price_cache_write_1h": ""}
    )

    _, cost = await _cost(
        _usage(
            prompt=10_000,
            completion=0,
            cached=0,
            cache_write=3_000,
            cache_write_1h=1_000,
        )
    )

    assert cost.input_details.cache_write == pytest.approx(
        (2_000 * 3.75 + 1_000 * 3) / 1e6
    )


@pytest.mark.anyio
async def test_long_context_tier_uses_long_context_cache_write_prices(model_config):
    model_config.update(
        {
            **_PRICING,
            **_LONG_CONTEXT,
            "price_scheme": "anthropic",
            "price_long_context_cache_write": "7.5",
            "price_long_context_cache_write_1h": "12",
        }
    )

    _, cost = await _cost(
        _usage(
            prompt=250_000,
            completion=0,
            cached=0,
            cache_write=100_000,
            cache_write_1h=40_000,
        )
    )

    assert cost.input_details.cache_write == pytest.approx(
        (60_000 * 7.5 + 40_000 * 12) / 1e6
    )
    assert cost.input_details.standard == pytest.approx(150_000 * 6 / 1e6)


@pytest.mark.anyio
async def test_long_context_cache_writes_fall_back_to_standard_cache_writes(
    model_config,
):
    model_config.update({**_PRICING, **_LONG_CONTEXT, "price_scheme": "anthropic"})

    _, cost = await _cost(
        _usage(
            prompt=250_000,
            completion=0,
            cached=0,
            cache_write=100_000,
            cache_write_1h=40_000,
        )
    )

    assert cost.input_details.cache_write == pytest.approx(
        (60_000 * 3.75 + 40_000 * 6) / 1e6
    )


@pytest.mark.anyio
async def test_no_cache_write_reports_none(model_config):
    model_config.update({**_PRICING, "price_scheme": "anthropic"})

    usage, cost = await _cost(
        _usage(prompt=1_000, completion=10, cached=0, cache_write=0)
    )

    assert usage.input_details.cache_write is None
    assert usage.input_details.standard == 1_000
    assert cost.input_details.cache_write is None


@pytest.mark.anyio
async def test_model_usage_has_no_cache_split(model_config):
    model_config.update(_PRICING)

    usage, cost = await _cost(ModelUsage(input_units="tokens", input=500, total=500))

    assert usage.input_details.standard == 500
    assert usage.input_details.cached is None
    assert usage.input_details.cache_write is None
    assert cost.input == pytest.approx(500 * 3 / 1e6)
