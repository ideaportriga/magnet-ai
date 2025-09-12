import asyncio
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import Any, Sequence

from bson import ObjectId
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.trace import format_span_id
from opentelemetry.trace.status import StatusCode

from services.observability.models import (
    ObservabilityConfig,
    ObservedConversation,
    ObservedFeatureInstance,
    ObservedGlobals,
    SpanExportMethod,
    SpanType,
    TraceObservabilityFields,
)
from services.observability.otel.attributes import (
    get_span_cost_details,
    get_span_description,
    get_span_extra_data,
    get_span_input_output,
    get_span_model,
    get_span_name,
    get_span_prompt_template,
    get_span_type,
    get_span_usage_details,
)
from services.observability.utils import (
    apply_utc_timezone,
    format_trace_id_as_mongo_id,
    get_dt_from_nanos,
    get_duration,
)

logger = getLogger(__name__)


@dataclass
class TraceToSave:
    spans: list[dict[str, Any]]
    root_span: dict[str, Any] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    name: str | None = None
    type: str | None = None
    status: str | None = None
    channel: str | None = None
    source: str | None = None
    extra_data: dict[str, Any] | None = None
    user_id: str | None = None
    chat_cost: float = 0.0
    embed_cost: float = 0.0
    rerank_cost: float = 0.0
    total_cost: float = 0.0


TraceAccumulator = dict[str, TraceToSave]
AnalyticsAccumulator = dict[str, dict[str, Any]]


class MongoDbSpanExporter(SpanExporter):
    def __init__(self):
        self._loop = asyncio.get_running_loop()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        logger.info(f"Exporting {len(spans)} spans")
        start_time = time.time()

        future = asyncio.run_coroutine_threadsafe(self._export_spans(spans), self._loop)
        future.result()

        end_time = time.time()
        logger.info(f"Exported {len(spans)} spans in {end_time - start_time} seconds")
        return SpanExportResult.SUCCESS

    async def _export_spans(self, spans: Sequence[ReadableSpan]):
        from stores import get_db_client

        self.db = get_db_client()
        try:
            trace_accumulator: TraceAccumulator = {}
            analytics_accumulator: AnalyticsAccumulator = {}
            for span in spans:
                # print(span.to_json())
                await self._export_span(span, trace_accumulator, analytics_accumulator)

            for trace_id, trace_patch in trace_accumulator.items():
                await self._upsert_trace(trace_id=trace_id, trace_patch=trace_patch)

            for analytics_id, analytics_patch in analytics_accumulator.items():
                await self._upsert_analytics(analytics_id, analytics_patch)
        except Exception:
            logger.error("Failed to export spans")
            traceback.print_exc()

    async def _export_span(
        self,
        span: ReadableSpan,
        trace_accumulator: TraceAccumulator,
        analytics_accumulator: AnalyticsAccumulator,
    ):
        span_context = span.context
        if not span_context:
            logger.warning("Span does not have a context, skipping export")
            return

        attributes = span.attributes
        if not attributes:
            logger.warning("Span does not have attributes, skipping export")
            return

        span_type = get_span_type(attributes)
        if not span_type:
            logger.warning("Span does not have a MagnetAI type, skipping export")
            return

        # Get config
        config = ObservabilityConfig.from_otel_attributes(attributes)
        if config.span_export_method == SpanExportMethod.IGNORE:
            return

        # Get span main references
        trace_id = format_trace_id_as_mongo_id(span_context.trace_id)
        span_id = format_span_id(span_context.span_id)
        span_parent_id = (
            format_span_id(span.parent.span_id) if span.parent else trace_id
        )

        if trace_id not in trace_accumulator:
            trace = trace_accumulator[trace_id] = TraceToSave(spans=[])
        else:
            trace = trace_accumulator[trace_id]

        # Get span timestamps
        span_start_time = apply_utc_timezone(get_dt_from_nanos(span.start_time))
        span_end_time = apply_utc_timezone(get_dt_from_nanos(span.end_time))

        # Get span status
        span_status = "success"
        span_status_message = None
        if span.status.status_code == StatusCode.ERROR:
            span_status = "error"
            span_status_message = _get_error_message(span)

        # Get global fields
        global_fields = ObservedGlobals.from_otel_attributes(attributes)

        # Get trace fields
        trace_fields = TraceObservabilityFields.from_otel_attributes(attributes)

        # Get conversation fields
        conversation = ObservedConversation.from_otel_attributes(attributes)

        # Get inputs and outputs
        input, output = get_span_input_output(attributes)

        model_details = get_span_model(attributes)
        usage_details = get_span_usage_details(attributes)
        usage_details = usage_details.model_dump() if usage_details else None
        cost_details = get_span_cost_details(attributes)
        cost_details = cost_details.model_dump() if cost_details else None
        extra_data = get_span_extra_data(attributes)

        trace.name = trace.name or trace_fields.name.value
        trace.type = trace.type or trace_fields.type.value
        trace.status = "error" if span_status == StatusCode.ERROR else None
        trace.channel = trace.channel or global_fields.channel.value
        trace.source = trace.source or global_fields.source.value
        # TODO: merge extra data
        trace.extra_data = trace.extra_data or trace_fields.extra_data.value
        trace.user_id = trace.user_id or global_fields.user_id.value

        if (
            config.span_export_method.value
            != SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
            or span_status == "error"
        ):
            trace.spans.append(
                {
                    "id": span_id,
                    "parent_id": span_parent_id,
                    "name": get_span_name(attributes),
                    "type": span_type,
                    "start_time": span_start_time,
                    "end_time": span_end_time,
                    "latency": get_duration(span_start_time, span_end_time),
                    "status": span_status,
                    "status_message": span_status_message,
                    "prompt_template": get_span_prompt_template(attributes),
                    "model": model_details,
                    "description": get_span_description(attributes),
                    "extra_data": extra_data,
                    "input": input,
                    "output": output,
                    "usage_details": usage_details,
                    "cost_details": cost_details,
                    "conversation_id": conversation.id.value,
                }
            )

        if span.name == "root":
            trace.root_span = {
                "start_time": span_start_time,
                "end_time": span_end_time,
            }
            trace.start_time = span_start_time
            trace.end_time = span_end_time
        else:
            if trace.start_time and span_start_time:
                trace.start_time = min(trace.start_time, span_start_time)
            elif span_start_time:
                trace.start_time = span_start_time
            if trace.end_time and span_end_time:
                trace.end_time = max(trace.end_time, span_end_time)
            elif span_end_time:
                trace.end_time = span_end_time

        span_total_cost_details = (
            cost_details.get("total") if cost_details else None
        ) or 0.0

        if span_type == SpanType.CHAT_COMPLETION:
            trace.chat_cost += span_total_cost_details
        elif span_type == SpanType.EMBEDDING:
            trace.embed_cost += span_total_cost_details
        elif span_type == SpanType.RERANKING:
            trace.rerank_cost += span_total_cost_details

        trace.total_cost += span_total_cost_details

        feature_instance = ObservedFeatureInstance.from_otel_attributes(attributes)
        if feature_instance:
            if feature_instance.id.value not in analytics_accumulator:
                analytics = analytics_accumulator[feature_instance.id.value] = {}
            else:
                analytics = analytics_accumulator[feature_instance.id.value]

            analytics.update(
                {
                    "feature_type": feature_instance.feature.type.value.value,
                    "feature_id": feature_instance.feature.id.value,
                    "feature_system_name": feature_instance.feature.system_name.value,
                    "feature_name": feature_instance.feature.display_name.value,
                    "feature_variant": feature_instance.feature.variant.value,
                    "trace_id": trace_id,
                    "channel": global_fields.channel.value,
                    "source": global_fields.source.value,
                    "user_id": global_fields.user_id.value,
                    "consumer_name": global_fields.consumer_name.value,
                    "consumer_type": global_fields.consumer_type.value,
                    "status": span_status,
                    "start_time": span_start_time,
                    "end_time": span_end_time,
                    "latency": get_duration(span_start_time, span_end_time),
                    "extra_data.input": input,
                    "extra_data.output": output,
                    "extra_data.model_details": model_details,
                    "extra_data.usage_details": usage_details,
                    "extra_data.cost_details": cost_details,
                    "conversation_id": conversation.id.value,
                }
            )
            if cost_details:
                analytics["cost"] = (analytics.get("cost") or 0.0) + (
                    cost_details.get("total") or 0.0
                )
            for key, value in (extra_data or {}).items():
                analytics.update({f"extra_data.{key}": value})
            for key, value in (global_fields.x_attributes.value or {}).items():
                analytics.update({f"x_attributes.{key}": value})
            for key, value in (conversation.data.value or {}).items():
                analytics.update({f"conversation_data.{key}": value})

            parent_feature_count = 0
            while cost_details:
                parent_feature_instance = ObservedFeatureInstance.from_otel_attributes(
                    attributes,
                    prefix=f"magnet_ai.parent_feature.{parent_feature_count}",
                )

                if not parent_feature_instance:
                    break

                if parent_feature_instance.id.value not in analytics_accumulator:
                    parent_analytics = analytics_accumulator[
                        parent_feature_instance.id.value
                    ] = {}
                else:
                    parent_analytics = analytics_accumulator[
                        parent_feature_instance.id.value
                    ]

                parent_analytics["cost"] = (parent_analytics.get("cost") or 0.0) + (
                    cost_details.get("total") or 0.0
                )

                parent_feature_count += 1

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    async def _upsert_trace(self, trace_id: str, trace_patch: TraceToSave):
        trace = await self.db.get_collection("traces").find_one(
            {"_id": ObjectId(trace_id)}
        )

        if trace:
            trace_start_time = apply_utc_timezone(trace.get("start_time"))
            trace_end_time = apply_utc_timezone(trace.get("end_time"))
            if trace_start_time and trace_patch.start_time:
                trace_start_time = min(trace_start_time, trace_patch.start_time)
            elif trace_patch.start_time:
                trace_start_time = trace_patch.start_time
            if trace_end_time and trace_patch.end_time:
                trace_end_time = max(trace_end_time, trace_patch.end_time)
            elif trace_patch.end_time:
                trace_end_time = trace_patch.end_time
        else:
            trace_start_time = trace_patch.start_time
            trace_end_time = trace_patch.end_time

        fields = {
            "$setOnInsert": {
                "status": "success",
                "status_message": None,
                "cost_details": {
                    "chat": 0.0,
                    "embed": 0.0,
                    "rerank": 0.0,
                    "total": 0.0,
                },
            },
            "$set": {
                "name": (trace and trace.get("name")) or trace_patch.name,
                "type": (trace and trace.get("type")) or trace_patch.type,
                "channel": (trace and trace.get("channel")) or trace_patch.channel,
                "source": (trace and trace.get("source")) or trace_patch.source,
                # TODO: need to merge extra data
                "extra_data": (trace and trace.get("extra_data"))
                or trace_patch.extra_data,
                "user_id": (trace and trace.get("user_id")) or trace_patch.user_id,
                "start_time": trace_start_time,
                "end_time": trace_end_time,
                "latency": get_duration(trace_start_time, trace_end_time),
            },
            "$inc": {
                "cost_details.chat": trace_patch.chat_cost,
                "cost_details.embed": trace_patch.embed_cost,
                "cost_details.rerank": trace_patch.rerank_cost,
                "cost_details.total": trace_patch.total_cost,
            },
        }

        if len(trace_patch.spans) > 0:
            fields["$push"] = {"spans": {"$each": []}}
            idle_span: dict[str, Any] | None = None
            if trace_patch.root_span:
                latest_existing_root_span_end_time = None
                if trace:
                    for existing_span in trace.get("spans", []):
                        if existing_span.get("parent_id") == trace_id:
                            if latest_existing_root_span_end_time is None:
                                latest_existing_root_span_end_time = existing_span.get(
                                    "end_time"
                                )
                            else:
                                latest_existing_root_span_end_time = max(
                                    latest_existing_root_span_end_time,
                                    existing_span.get("end_time"),
                                )
                    latest_existing_root_span_end_time = apply_utc_timezone(
                        latest_existing_root_span_end_time
                    )
                    if latest_existing_root_span_end_time:
                        idle_span = {
                            "id": format_span_id(
                                RandomIdGenerator().generate_span_id()
                            ),
                            "parent_id": trace_id,
                            "type": "idle",
                            "start_time": latest_existing_root_span_end_time,
                            "end_time": trace_patch.root_span.get("start_time"),
                            "latency": get_duration(
                                latest_existing_root_span_end_time,
                                trace_patch.root_span.get("start_time"),
                            ),
                        }
            if idle_span:
                fields["$push"]["spans"]["$each"].append(idle_span)
            fields["$push"]["spans"]["$each"].extend(trace_patch.spans)

        await self.db.get_collection("traces").update_one(
            {"_id": ObjectId(trace_id)}, fields, upsert=True
        )

    async def _upsert_analytics(self, id: str, patch: dict):
        patch = {k: v for k, v in patch.items() if v is not None}
        cost = patch.pop("cost", 0.0)
        fields = {}
        if patch != {}:
            fields["$set"] = patch
        fields["$inc"] = {"cost": cost}
        await self.db.get_collection("metrics").update_one(
            {"_id": ObjectId(id)}, fields, upsert=True
        )


def _get_error_message(span: ReadableSpan) -> str:
    for event in span.events:
        if event.name == "exception" and event.attributes:
            return (
                str(event.attributes.get("exception.message"))
                + "\n"
                + str(event.attributes.get("exception.stacktrace"))
            )

    return ""
