from asyncio.log import logger
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Unpack

from openai.types.completion_usage import CompletionUsage
from opentelemetry.trace import format_trace_id

from openai_model.utils import get_model_by_system_name
from services.ai_services.models import ModelUsage
from services.observability.models import (
    CostDetails,
    CostInputDetails,
    CostOutputDetails,
    DecoratorParams,
    UsageDetails,
    UsageInputDetails,
    UsageOutputDetails,
)


@dataclass
class ModelPricing:
    input_units: str = "tokens"
    input_standard_price_per_unit: float = 0.0
    input_cached_price_per_unit: float = 0.0
    output_units: str = "tokens"
    output_standard_price_per_unit: float = 0.0
    output_reasoning_price_per_unit: float = 0.0


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
            standard_input_tokens = usage.prompt_tokens - (cached_input_tokens or 0)
            total_input_tokens = usage.prompt_tokens
        elif isinstance(usage, ModelUsage):
            cached_input_tokens = None
            standard_input_tokens = usage.input
            total_input_tokens = usage.input
        else:
            cached_input_tokens = None
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
            ),
            output=total_output_tokens,
            output_details=UsageOutputDetails(
                units=output_units,
                standard=standard_output_tokens,
                reasoning=reasoning_output_tokens,
            ),
            total=total_tokens,
        )

        # Calculate input cost
        if input_units == pricing.input_units:
            cached_input_cost = (
                (pricing.input_cached_price_per_unit * cached_input_tokens)
                if cached_input_tokens is not None
                else None
            )
            standard_input_cost = (
                (pricing.input_standard_price_per_unit * standard_input_tokens)
                if standard_input_tokens is not None
                else None
            )
            total_input_cost = (
                (standard_input_cost + (cached_input_cost or 0))
                if standard_input_cost is not None
                else None
            )
        else:
            cached_input_cost = None
            standard_input_cost = None
            total_input_cost = None

        # Calculate output cost
        if output_units == pricing.output_units:
            reasoning_output_cost = (
                (pricing.output_reasoning_price_per_unit * reasoning_output_tokens)
                if reasoning_output_tokens is not None
                else None
            )
            standard_output_cost = (
                (pricing.output_standard_price_per_unit * standard_output_tokens)
                if standard_output_tokens is not None
                else None
            )
            total_output_cost = (
                (standard_output_cost + (reasoning_output_cost or 0))
                if standard_output_cost is not None
                else None
            )
        else:
            reasoning_output_cost = None
            standard_output_cost = None
            total_output_cost = None

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

    output_unit_name = model_config.get("price_output_unit_name") or "tokens"
    output_standard_price_per_unit = float(model_config.get("price_output") or 0.0)
    output_standard_unit_count = int(
        model_config.get("price_standard_output_unit_count") or 1000000,
    )
    output_reasoning_price_per_unit = float(model_config.get("price_reasoning") or 0.0)
    output_reasoning_unit_count = int(
        model_config.get("price_reasoning_output_unit_count") or 1000000,
    )

    return ModelPricing(
        input_units=input_unit_name,
        input_standard_price_per_unit=input_standard_price_per_unit
        / input_standard_unit_count,
        input_cached_price_per_unit=input_cached_price_per_unit
        / input_cached_unit_count,
        output_units=output_unit_name,
        output_standard_price_per_unit=output_standard_price_per_unit
        / output_standard_unit_count,
        output_reasoning_price_per_unit=output_reasoning_price_per_unit
        / output_reasoning_unit_count,
    )


def format_trace_id_as_mongo_id(trace_id: int) -> str:
    return format_trace_id(trace_id)[8:]


def format_trace_id_as_uuid(trace_id: int) -> str:
    """Convert OpenTelemetry trace ID to UUID format."""
    trace_id_hex = format_trace_id(trace_id)
    # Insert UUID dashes: 8-4-4-4-12
    return f"{trace_id_hex[:8]}-{trace_id_hex[8:12]}-{trace_id_hex[12:16]}-{trace_id_hex[16:20]}-{trace_id_hex[20:]}"
