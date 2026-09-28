"""Catalog token pricing used by observability cost calculation.

Kept free of observability / DB imports so it can be used without pulling in
the tracing stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelPricing:
    input_units: str = "tokens"
    input_standard_price_per_unit: float = 0.0
    input_cached_price_per_unit: float = 0.0
    # Pricing scheme (basic | openai | anthropic) decides which cache write
    # prices apply. None = no price for it; bill those writes at input price.
    scheme: str = "basic"
    input_cache_write_price_per_unit: float | None = None
    input_cache_write_1h_price_per_unit: float | None = None
    output_units: str = "tokens"
    output_standard_price_per_unit: float = 0.0
    # Long-context pricing: applied when total input tokens exceed threshold.
    long_context_threshold: int | None = None
    long_context_input_price_per_unit: float = 0.0
    long_context_input_cached_price_per_unit: float = 0.0
    long_context_input_cache_write_price_per_unit: float | None = None
    long_context_input_cache_write_1h_price_per_unit: float | None = None
    long_context_output_price_per_unit: float = 0.0


def _optional_price(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _per_unit(price: float | None, unit_count: int) -> float | None:
    return price / unit_count if price is not None else None


def _get_model_pricing(model_config: dict | None) -> ModelPricing:
    if not model_config:
        return ModelPricing()

    input_unit_name = model_config.get("price_input_unit_name") or "tokens"
    input_standard_price_per_unit = float(model_config.get("price_input") or 0.0)
    input_standard_unit_count = int(
        model_config.get("price_standard_input_unit_count") or 1000000,
    )
    input_cached_price_per_unit = float(model_config.get("price_cached") or 0.0)
    input_cached_unit_count = int(
        model_config.get("price_cached_input_unit_count") or 1000000,
    )
    # The scheme decides which cache write prices apply: basic has none (cache
    # writes bill at the input price), openai a single one, anthropic a
    # 5-minute (price_cache_write) and a 1-hour one. They share the cached
    # input unit count.
    scheme = model_config.get("price_scheme") or "basic"
    has_cache_write = scheme in ("openai", "anthropic")
    has_cache_write_1h = scheme == "anthropic"
    input_cache_write_price = (
        _optional_price(model_config.get("price_cache_write"))
        if has_cache_write
        else None
    )
    input_cache_write_1h_price = (
        _optional_price(model_config.get("price_cache_write_1h"))
        if has_cache_write_1h
        else None
    )

    output_unit_name = model_config.get("price_output_unit_name") or "tokens"
    output_standard_price_per_unit = float(model_config.get("price_output") or 0.0)
    output_standard_unit_count = int(
        model_config.get("price_standard_output_unit_count") or 1000000,
    )

    # Long-context pricing reuses the standard unit counts (only the per-unit
    # price differs); a missing threshold disables the long-context tier.
    raw_long_context_threshold = model_config.get("price_long_context_threshold")
    long_context_threshold = (
        int(raw_long_context_threshold)
        if raw_long_context_threshold not in (None, "")
        else None
    )
    long_context_input_price = float(
        model_config.get("price_long_context_input") or 0.0
    )
    long_context_cached_price = float(
        model_config.get("price_long_context_cached") or 0.0
    )
    long_context_output_price = float(
        model_config.get("price_long_context_output") or 0.0
    )
    # Fall back to the standard cache write prices; if neither is set the
    # cost calculation bills cache writes at the (long-context) input price.
    long_context_cache_write_price = (
        _optional_price(model_config.get("price_long_context_cache_write"))
        if has_cache_write
        else None
    )
    if long_context_cache_write_price is None:
        long_context_cache_write_price = input_cache_write_price
    long_context_cache_write_1h_price = (
        _optional_price(model_config.get("price_long_context_cache_write_1h"))
        if has_cache_write_1h
        else None
    )
    if long_context_cache_write_1h_price is None:
        long_context_cache_write_1h_price = input_cache_write_1h_price

    return ModelPricing(
        input_units=input_unit_name,
        input_standard_price_per_unit=input_standard_price_per_unit
        / input_standard_unit_count,
        input_cached_price_per_unit=input_cached_price_per_unit
        / input_cached_unit_count,
        scheme=scheme,
        input_cache_write_price_per_unit=_per_unit(
            input_cache_write_price, input_cached_unit_count
        ),
        input_cache_write_1h_price_per_unit=_per_unit(
            input_cache_write_1h_price, input_cached_unit_count
        ),
        output_units=output_unit_name,
        output_standard_price_per_unit=output_standard_price_per_unit
        / output_standard_unit_count,
        long_context_threshold=long_context_threshold,
        long_context_input_price_per_unit=long_context_input_price
        / input_standard_unit_count,
        long_context_input_cached_price_per_unit=long_context_cached_price
        / input_cached_unit_count,
        long_context_input_cache_write_price_per_unit=_per_unit(
            long_context_cache_write_price, input_cached_unit_count
        ),
        long_context_input_cache_write_1h_price_per_unit=_per_unit(
            long_context_cache_write_1h_price, input_cached_unit_count
        ),
        long_context_output_price_per_unit=long_context_output_price
        / output_standard_unit_count,
    )


@dataclass
class TokenCostBreakdown:
    """USD cost of one token-priced call, split like ``CostDetails``."""

    standard: float
    cached: float
    cache_write: float
    output: float

    @property
    def total(self) -> float:
        return self.standard + self.cached + self.cache_write + self.output


def price_token_usage(
    pricing: ModelPricing,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_write_1h_tokens: int = 0,
) -> TokenCostBreakdown:
    """Price one call's token usage — the single pricing core.

    Cache reads and writes are both a subset of ``prompt_tokens``; the rest is
    standard input. ``cache_write_1h_tokens`` is the 1-hour-TTL share of the
    writes (Anthropic); the remainder are 5-minute writes. The long-context tier
    applies when ``prompt_tokens`` exceeds the threshold. A missing cache write
    price bills writes at the input price; under the anthropic scheme a missing
    1-hour price does too, elsewhere 1-hour writes bill like any other write.
    """
    long_context = (
        pricing.long_context_threshold is not None
        and prompt_tokens > pricing.long_context_threshold
    )
    if long_context:
        input_price = pricing.long_context_input_price_per_unit
        cached_price = pricing.long_context_input_cached_price_per_unit
        cache_write_price = pricing.long_context_input_cache_write_price_per_unit
        cache_write_1h_price = pricing.long_context_input_cache_write_1h_price_per_unit
        output_price = pricing.long_context_output_price_per_unit
    else:
        input_price = pricing.input_standard_price_per_unit
        cached_price = pricing.input_cached_price_per_unit
        cache_write_price = pricing.input_cache_write_price_per_unit
        cache_write_1h_price = pricing.input_cache_write_1h_price_per_unit
        output_price = pricing.output_standard_price_per_unit
    if cache_write_price is None:
        cache_write_price = input_price
    if cache_write_1h_price is None:
        cache_write_1h_price = (
            input_price if pricing.scheme == "anthropic" else cache_write_price
        )

    prompt = max(0, prompt_tokens)
    cached = max(0, min(cached_tokens, prompt))
    written = max(0, min(cache_write_tokens, prompt - cached))
    written_1h = max(0, min(cache_write_1h_tokens, written))
    return TokenCostBreakdown(
        standard=input_price * (prompt - cached - written),
        cached=cached_price * cached,
        cache_write=cache_write_price * (written - written_1h)
        + cache_write_1h_price * written_1h,
        output=output_price * max(0, completion_tokens),
    )
