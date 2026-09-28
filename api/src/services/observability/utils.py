from asyncio.log import logger
from datetime import UTC, datetime
from typing import Any, Dict, Unpack

from openai.types.completion_usage import CompletionUsage
from opentelemetry.trace import format_trace_id

from openai_model.utils import get_model_by_system_name
from services.ai_services.models import ModelUsage
from services.ai_services.pricing import (  # noqa: F401 — re-exported
    ModelPricing,
    _get_model_pricing,
    price_token_usage,
)
from services.observability.models import (
    CostDetails,
    CostInputDetails,
    CostOutputDetails,
    DecoratorParams,
    UsageDetails,
    UsageInputDetails,
    UsageOutputDetails,
)


def observability_overrides(
    trace_id: str | None = None,
    **decor_params: Unpack[DecoratorParams],
) -> dict[str, Any]:
    return {
        "_observability_overrides": {
            "trace_id": trace_id,
            "decorator": decor_params,
        }
    }


def get_timestamp():
    return datetime.now(UTC)


def get_dt_from_nanos(nanos: int | None) -> datetime | None:
    if nanos is None:
        return None
    return datetime.fromtimestamp(nanos / 1_000_000_000, UTC)


def get_nanos(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return int(dt.timestamp() * 1_000_000_000)


def apply_utc_timezone(dt: datetime | None) -> datetime | None:
    return dt.replace(tzinfo=UTC) if dt else None


def get_duration(
    start_time: datetime | None, end_time: datetime | None
) -> float | None:
    if start_time is None or end_time is None:
        return None
    return (end_time - start_time).total_seconds() * 1000


def extract_x_attributes_from_request(args, kwargs) -> Dict[str, Any]:
    """Safely extract x_attributes from request headers in args/kwargs."""
    x_attributes = {}
    try:
        request = None
        if args:
            for arg in args:
                if hasattr(arg, "headers"):
                    request = arg
                    break
        if not request and "request" in kwargs:
            request = kwargs["request"]
        if request and hasattr(request, "headers"):
            try:
                for k, v in request.headers.items():
                    if k.lower().startswith("x-attrib-"):
                        attrib_key = k[9:]
                        x_attributes[attrib_key] = v
            except Exception:
                pass
    except Exception:
        pass
    return x_attributes


def merge_dicts(
    a: dict[str, Any] | None,
    b: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if a and b:
        return {**a, **b}
    if a:
        return a
    if b:
        return b
    return {}


async def get_usage_and_cost_details(
    usage: CompletionUsage | ModelUsage | None,
    model_system_name: str | None,
) -> tuple[UsageDetails | None, CostDetails | None]:
    try:
        if model_system_name:
            model_config = await get_model_by_system_name(model_system_name)
        else:
            model_config = None

        pricing = _get_model_pricing(model_config)

        # Calculate input tokens
        if isinstance(usage, CompletionUsage):
            cached_input_tokens = (
                usage.prompt_tokens_details.cached_tokens
                if usage.prompt_tokens_details
                and usage.prompt_tokens_details.cached_tokens is not None
                else None
            )
            cache_write_input_tokens = _get_cache_write_tokens(usage)
            cache_write_1h_input_tokens = _get_cache_write_1h_tokens(usage)
            # Cache reads and writes are both a subset of prompt_tokens.
            standard_input_tokens = (
                usage.prompt_tokens
                - (cached_input_tokens or 0)
                - (cache_write_input_tokens or 0)
            )
            total_input_tokens = usage.prompt_tokens
        elif isinstance(usage, ModelUsage):
            cached_input_tokens = None
            cache_write_input_tokens = None
            cache_write_1h_input_tokens = None
            standard_input_tokens = usage.input
            total_input_tokens = usage.input
        else:
            cached_input_tokens = None
            cache_write_input_tokens = None
            cache_write_1h_input_tokens = None
            standard_input_tokens = None
            total_input_tokens = None

        # Calculate output tokens
        if isinstance(usage, CompletionUsage):
            reasoning_output_tokens = (
                usage.completion_tokens_details.reasoning_tokens
                if usage.completion_tokens_details
                and usage.completion_tokens_details.reasoning_tokens is not None
                else None
            )
            standard_output_tokens = (
                (usage.completion_tokens - (reasoning_output_tokens or 0))
                if usage.completion_tokens is not None
                else None
            )
            total_output_tokens = usage.completion_tokens
        else:
            reasoning_output_tokens = None
            standard_output_tokens = None
            total_output_tokens = None

        # Calculate total tokens
        if isinstance(usage, CompletionUsage):
            total_tokens = usage.total_tokens
        elif isinstance(usage, ModelUsage):
            total_tokens = usage.total
        else:
            total_tokens = None

        # Get usage units
        input_units = usage.input_units if isinstance(usage, ModelUsage) else "tokens"
        output_units = "tokens"

        # Prepare usage details
        usage_details = UsageDetails(
            input=total_input_tokens,
            input_details=UsageInputDetails(
                units=input_units,
                standard=standard_input_tokens,
                cached=cached_input_tokens,
                cache_write=cache_write_input_tokens,
            ),
            output=total_output_tokens,
            output_details=UsageOutputDetails(
                units=output_units,
                standard=standard_output_tokens,
                reasoning=reasoning_output_tokens,
            ),
            total=total_tokens,
        )

        # Price the call with the shared pricing core, then
        # blank out whatever the usage didn't report.
        breakdown = price_token_usage(
            pricing,
            prompt_tokens=total_input_tokens or 0,
            completion_tokens=total_output_tokens or 0,
            cached_tokens=cached_input_tokens or 0,
            cache_write_tokens=cache_write_input_tokens or 0,
            cache_write_1h_tokens=cache_write_1h_input_tokens or 0,
        )

        # Calculate input cost
        if input_units == pricing.input_units and standard_input_tokens is not None:
            cached_input_cost = (
                breakdown.cached if cached_input_tokens is not None else None
            )
            cache_write_input_cost = (
                breakdown.cache_write if cache_write_input_tokens is not None else None
            )
            standard_input_cost = breakdown.standard
            total_input_cost = (
                standard_input_cost
                + (cached_input_cost or 0)
                + (cache_write_input_cost or 0)
            )
        else:
            cached_input_cost = None
            cache_write_input_cost = None
            standard_input_cost = None
            total_input_cost = None

        # Calculate output cost — reasoning tokens are billed at the standard
        # output rate (no separate reasoning-output price).
        if output_units == pricing.output_units and total_output_tokens is not None:
            standard_output_cost = breakdown.output
        else:
            standard_output_cost = None
        reasoning_output_cost = None
        total_output_cost = standard_output_cost

        # Calculate total cost and prepare cost details
        total_cost = (
            ((total_input_cost or 0) + (total_output_cost or 0))
            if total_input_cost is not None or total_output_cost is not None
            else None
        )
        cost_details = CostDetails(
            input=total_input_cost,
            input_details=CostInputDetails(
                standard=standard_input_cost,
                cached=cached_input_cost,
                cache_write=cache_write_input_cost,
            ),
            output=total_output_cost,
            output_details=CostOutputDetails(
                standard=standard_output_cost,
                reasoning=reasoning_output_cost,
            ),
            total=total_cost,
        )

        return usage_details, cost_details
    except Exception as e:
        logger.warning(f"Failed to get usage and cost details from LLM response: {e}")
        return None, None


def _get_cache_write_tokens(usage: CompletionUsage) -> int | None:
    """Prompt-cache write (creation) tokens off a litellm/OpenAI usage object.

    litellm normalizes Anthropic/Bedrock cache writes into
    ``prompt_tokens_details.cache_creation_tokens`` (the attribute is absent,
    not ``None``, when unset); OpenAI/Azure report them as
    ``prompt_tokens_details.cache_write_tokens``, which litellm passes through
    as-is; the raw Anthropic name is the last fallback. Zero is reported as
    ``None`` so providers without prompt-cache writes show no row.
    """
    details = usage.prompt_tokens_details
    tokens = getattr(details, "cache_creation_tokens", None) if details else None
    if not tokens and details:
        tokens = getattr(details, "cache_write_tokens", None)
    if not tokens:
        tokens = getattr(usage, "cache_creation_input_tokens", None)
    return int(tokens) if tokens else None


def _get_cache_write_1h_tokens(usage: CompletionUsage) -> int | None:
    """The 1-hour-TTL share of the cache write tokens (Anthropic only).

    litellm reports it as
    ``prompt_tokens_details.cache_creation_token_details.ephemeral_1h_input_tokens``;
    the rest of the cache write tokens are 5-minute writes.
    """
    details = getattr(usage.prompt_tokens_details, "cache_creation_token_details", None)
    tokens = getattr(details, "ephemeral_1h_input_tokens", None) if details else None
    return int(tokens) if tokens else None


def format_trace_id_as_mongo_id(trace_id: int) -> str:
    return format_trace_id(trace_id)[8:]


def format_trace_id_as_uuid(trace_id: int) -> str:
    """Convert OpenTelemetry trace ID to UUID format."""
    trace_id_hex = format_trace_id(trace_id)
    # Insert UUID dashes: 8-4-4-4-12
    return f"{trace_id_hex[:8]}-{trace_id_hex[8:12]}-{trace_id_hex[12:16]}-{trace_id_hex[16:20]}-{trace_id_hex[20:]}"
