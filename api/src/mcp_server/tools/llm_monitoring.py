"""MCP tools: LLM call monitoring and cost analysis.

Two tools:
  1. llm_usage_summary  — aggregate stats for a template or all calls
  2. llm_calls_list     — paginated individual call records with extra_data
"""

from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field

from core.config.app import alchemy
from services.observability.models import FeatureType
from services.observability.services import (
    get_metrics_by_feature_type,
    summarize_llm_metrics,
)
from type_defs.pagination import FilterObject, OffsetPaginationRequest

logger = getLogger(__name__)

_LLM_FEATURE_TYPES = [FeatureType.PROMPT_TEMPLATE, FeatureType.CHAT_COMPLETION]


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class LlmUsageSummaryOut(BaseModel):
    """Aggregate LLM call statistics."""

    total_calls: int
    avg_cost: float = Field(description="Average cost per call in USD")
    total_cost: float = Field(description="Sum of all call costs in USD")
    error_rate: float = Field(description="Fraction of calls that errored (0–1)")
    avg_latency: float = Field(description="Average latency in milliseconds")


class LlmCallRecordOut(BaseModel):
    """One LLM call record."""

    id: str
    name: str
    template_system_name: Optional[str] = Field(
        None, description="Prompt template system_name that made this call"
    )
    variant: Optional[str] = None
    cost: Optional[float] = Field(None, description="Call cost in USD")
    latency: Optional[float] = Field(None, description="Latency in milliseconds")
    start_time: Optional[datetime] = None
    status: Optional[str] = Field(None, description="'success' | 'error' | 'failure'")
    consumer_type: Optional[str] = Field(
        None, description="Who made the call: 'runtime', 'evaluation', 'preview', etc."
    )
    extra_data: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Observability payload. Contains 'input' and 'output' keys when the "
            "template's observability_level is 'full'."
        ),
    )


class LlmCallsPageOut(BaseModel):
    """Paginated list of LLM call records."""

    items: list[LlmCallRecordOut]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_filter(
    *,
    template_system_name: str | None,
    status: str | None,
    start_time_after: str | None,
    consumer_type: str | None,
) -> FilterObject:
    raw: dict[str, Any] = {}
    if template_system_name:
        raw["feature_system_name"] = {"$eq": template_system_name}
    if status:
        raw["status"] = {"$eq": status}
    if start_time_after:
        raw["start_time"] = {"$gte": start_time_after}
    if consumer_type:
        raw["consumer_type"] = {"$eq": consumer_type}
    return FilterObject.model_validate(raw)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def llm_usage_summary(
    template_system_name: Optional[str] = None,
) -> LlmUsageSummaryOut:
    """Get aggregate LLM call statistics: total calls, average and total cost,
    average latency, and error rate.

    Optionally filter to one prompt template by passing its ``system_name``
    (e.g. ``DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS``). Omit to get
    stats across all LLM calls.

    Use this to answer questions like "how much does template X cost?" or
    "what is the error rate for our research feature?".
    """
    async with alchemy.get_session() as session:
        filters = _build_filter(
            template_system_name=template_system_name,
            status=None,
            start_time_after=None,
            consumer_type=None,
        )
        result = await summarize_llm_metrics(session, filters)

        if not hasattr(result, "total_calls"):
            return LlmUsageSummaryOut(
                total_calls=0,
                avg_cost=0.0,
                total_cost=0.0,
                error_rate=0.0,
                avg_latency=0.0,
            )

        return LlmUsageSummaryOut(
            total_calls=result.total_calls,
            avg_cost=result.avg_cost,
            total_cost=result.total_cost,
            error_rate=result.error_rate,
            avg_latency=result.avg_latency,
        )


async def llm_calls_list(
    template_system_name: Optional[str] = None,
    start_time_after: Annotated[
        Optional[str],
        Field(
            description="ISO 8601 datetime — return calls after this time (e.g. 2026-01-01T00:00:00Z)"
        ),
    ] = None,
    status: Annotated[
        Optional[str],
        Field(description="Filter by call status: 'success', 'error', or 'failure'"),
    ] = None,
    consumer_type: Annotated[
        Optional[str],
        Field(
            description=(
                "Filter by who made the call — e.g. 'runtime' for production API calls, "
                "'evaluation' for evaluation job calls, 'preview' for UI test calls"
            )
        ),
    ] = None,
    limit: Annotated[
        int, Field(ge=1, le=100, description="Max records to return")
    ] = 20,
    offset: Annotated[
        int, Field(ge=0, description="Records to skip for pagination")
    ] = 0,
) -> LlmCallsPageOut:
    """List individual LLM call records (chat completions only), most recent first.

    Each record includes cost, latency, variant, status, and ``extra_data``.
    When the prompt template's ``observability_level`` is ``full``, ``extra_data``
    contains ``input`` and ``output`` keys with the actual prompt and response.

    Use ``consumer_type`` to separate runtime production calls from evaluation
    job calls or UI preview/test calls.
    """
    async with alchemy.get_session() as session:
        filters = _build_filter(
            template_system_name=template_system_name,
            status=status,
            start_time_after=start_time_after,
            consumer_type=consumer_type,
        )
        data = OffsetPaginationRequest(
            limit=limit,
            offset=offset,
            sort="start_time",
            order=-1,
            filters=filters,
        )
        result = await get_metrics_by_feature_type(session, _LLM_FEATURE_TYPES, data)

        items = [
            LlmCallRecordOut(
                id=str(item.get("_id", "")),
                name=item.get("name", ""),
                template_system_name=item.get("feature_system_name"),
                variant=item.get("variant"),
                cost=item.get("cost"),
                latency=item.get("latency"),
                start_time=item.get("start_time"),
                status=item.get("status"),
                consumer_type=item.get("consumer_type"),
                extra_data=item.get("extra_data"),
            )
            for item in (result.get("items") or [])
        ]

        return LlmCallsPageOut(
            items=items,
            total=result.get("total", 0),
            limit=result.get("limit", limit),
            offset=result.get("offset", offset),
        )
