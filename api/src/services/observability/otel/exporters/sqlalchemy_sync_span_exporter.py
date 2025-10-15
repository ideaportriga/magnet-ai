import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import Any, Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.trace import format_span_id
from opentelemetry.trace.status import StatusCode
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from core.db.models.metric import Metric
from core.db.models.trace import Trace
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


def _serialize_for_json(obj: Any) -> Any:
    """Convert datetime objects and other non-JSON-serializable objects to JSON-compatible format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif hasattr(obj, "isoformat"):  # Handle other datetime-like objects
        return obj.isoformat()
    else:
        return obj


def _to_datetime(dt: Any) -> datetime | None:
    """Convert any datetime-like object to datetime."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    # Handle advanced_alchemy DateTimeUTC type
    if hasattr(dt, "replace") and hasattr(dt, "year"):
        return dt.replace(tzinfo=None) if hasattr(dt, "tzinfo") and dt.tzinfo else dt
    return dt


def _safe_min_datetime(dt1: Any, dt2: datetime | None) -> datetime | None:
    """Safely compare two datetime objects."""
    if dt1 is None:
        return dt2
    if dt2 is None:
        return _to_datetime(dt1)
    dt1_converted = _to_datetime(dt1)
    if dt1_converted is None:
        return dt2
    return min(dt1_converted, dt2)


def _safe_max_datetime(dt1: Any, dt2: datetime | None) -> datetime | None:
    """Safely compare two datetime objects."""
    if dt1 is None:
        return dt2
    if dt2 is None:
        return _to_datetime(dt1)
    dt1_converted = _to_datetime(dt1)
    if dt1_converted is None:
        return dt2
    return max(dt1_converted, dt2)


def _safe_max_span_time(span_time: Any) -> datetime | None:
    """Safely extract datetime from span data."""
    if span_time is None:
        return None
    if isinstance(span_time, datetime):
        return span_time
    # Convert from ISO string or other formats
    if isinstance(span_time, str):
        try:
            return datetime.fromisoformat(span_time.replace("Z", "+00:00"))
        except Exception:
            return None
    return _to_datetime(span_time)


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


class SqlAlchemySyncSpanExporter(SpanExporter):
    """Synchronous SQLAlchemy span exporter to avoid async event loop conflicts."""

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of database connection."""
        if self._initialized:
            return

        try:
            from core.config.app import settings

            # Create synchronous engine for the exporter
            # Use sync_url which already handles converting async drivers to sync
            database_url = settings.db.sync_url

            self._engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
            self._session_factory = sessionmaker(bind=self._engine)
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy sync exporter: {e}")
            raise

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        logger.info(f"Exporting {len(spans)} spans")
        start_time = time.time()

        try:
            self._ensure_initialized()
            self._export_spans_sync(spans)
        except Exception as e:
            logger.error(f"Unexpected error during span export: {e}")
            traceback.print_exc()
            return SpanExportResult.FAILURE

        end_time = time.time()
        logger.info(f"Exported {len(spans)} spans in {end_time - start_time} seconds")
        return SpanExportResult.SUCCESS

    def _export_spans_sync(self, spans: Sequence[ReadableSpan]):
        """Synchronous span export."""
        if not self._session_factory:
            logger.error("Session factory not initialized")
            return

        with self._session_factory() as session:
            try:
                trace_accumulator: TraceAccumulator = {}
                analytics_accumulator: AnalyticsAccumulator = {}

                for span in spans:
                    self._export_span_sync(
                        span, trace_accumulator, analytics_accumulator
                    )

                for trace_id, trace_patch in trace_accumulator.items():
                    self._upsert_trace_sync(
                        session, trace_id=trace_id, trace_patch=trace_patch
                    )

                for analytics_id, analytics_patch in analytics_accumulator.items():
                    self._upsert_metrics_sync(session, analytics_id, analytics_patch)

                session.commit()
            except Exception:
                logger.error("Failed to export spans")
                traceback.print_exc()
                session.rollback()
                raise

    def _export_span_sync(
        self,
        span: ReadableSpan,
        trace_accumulator: TraceAccumulator,
        analytics_accumulator: AnalyticsAccumulator,
    ):
        """Synchronous version of _export_span."""
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
            span_data = {
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
            # Serialize all datetime objects in span data for JSON storage
            trace.spans.append(_serialize_for_json(span_data))

        if span.name == "root":
            trace.root_span = _serialize_for_json(
                {
                    "start_time": span_start_time,
                    "end_time": span_end_time,
                }
            )
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

            # Prepare conversation data - serialize datetime objects
            conversation_data = _serialize_for_json(dict(conversation.data.value or {}))

            # Prepare extra data - serialize datetime objects
            full_extra_data = _serialize_for_json(
                {
                    "input": input,
                    "output": output,
                    "model_details": model_details,
                    "usage_details": usage_details,
                    "cost_details": cost_details,
                }
            )
            for key, value in (extra_data or {}).items():
                full_extra_data[key] = _serialize_for_json(value)
            for key, value in (global_fields.x_attributes.value or {}).items():
                full_extra_data[f"x_attributes.{key}"] = _serialize_for_json(value)

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
                    "conversation_id": conversation.id.value,
                    "conversation_data": conversation_data,
                    "extra_data": full_extra_data,
                }
            )
            if cost_details:
                analytics["cost"] = (analytics.get("cost") or 0.0) + (
                    cost_details.get("total") or 0.0
                )

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

    def _upsert_trace_sync(self, session, trace_id: str, trace_patch: TraceToSave):
        """Synchronous version of _upsert_trace."""
        # Check if trace exists
        existing_trace = session.execute(
            select(Trace).where(Trace.id == trace_id)
        ).scalar_one_or_none()

        if existing_trace:
            # Update existing trace
            trace_start_time = _safe_min_datetime(
                existing_trace.start_time, trace_patch.start_time
            )
            trace_end_time = _safe_max_datetime(
                existing_trace.end_time, trace_patch.end_time
            )

            # Merge spans
            existing_spans = existing_trace.spans or []
            new_spans = []

            # Add idle span if needed
            if trace_patch.root_span and existing_spans:
                latest_existing_root_span_end_time = None
                for existing_span in existing_spans:
                    if existing_span.get("parent_id") == trace_id:
                        span_end_time = _safe_max_span_time(
                            existing_span.get("end_time")
                        )
                        if span_end_time:
                            if latest_existing_root_span_end_time is None:
                                latest_existing_root_span_end_time = span_end_time
                            else:
                                latest_existing_root_span_end_time = max(
                                    latest_existing_root_span_end_time,
                                    span_end_time,
                                )

                if latest_existing_root_span_end_time:
                    idle_span = {
                        "id": format_span_id(RandomIdGenerator().generate_span_id()),
                        "parent_id": trace_id,
                        "type": "idle",
                        "start_time": latest_existing_root_span_end_time,
                        "end_time": trace_patch.root_span.get("start_time"),
                        "latency": get_duration(
                            latest_existing_root_span_end_time,
                            trace_patch.root_span.get("start_time"),
                        ),
                    }
                    new_spans.append(_serialize_for_json(idle_span))

            new_spans.extend(trace_patch.spans)
            all_spans = existing_spans + new_spans

            # Update cost details
            existing_cost_details = existing_trace.cost_details or {
                "chat": 0.0,
                "embed": 0.0,
                "rerank": 0.0,
                "total": 0.0,
            }

            updated_cost_details = {
                "chat": existing_cost_details.get("chat", 0.0) + trace_patch.chat_cost,
                "embed": existing_cost_details.get("embed", 0.0)
                + trace_patch.embed_cost,
                "rerank": existing_cost_details.get("rerank", 0.0)
                + trace_patch.rerank_cost,
                "total": existing_cost_details.get("total", 0.0)
                + trace_patch.total_cost,
            }

            # Update the existing trace
            session.execute(
                update(Trace)
                .where(Trace.id == trace_id)
                .values(
                    name=existing_trace.name or trace_patch.name,
                    type=existing_trace.type or trace_patch.type,
                    channel=existing_trace.channel or trace_patch.channel,
                    source=existing_trace.source or trace_patch.source,
                    extra_data=_serialize_for_json(
                        existing_trace.extra_data or trace_patch.extra_data
                    ),
                    user_id=existing_trace.user_id or trace_patch.user_id,
                    start_time=trace_start_time,
                    end_time=trace_end_time,
                    latency=get_duration(
                        _to_datetime(trace_start_time), _to_datetime(trace_end_time)
                    ),
                    cost_details=updated_cost_details,
                    spans=all_spans if new_spans else existing_trace.spans,
                )
            )
        else:
            # Create new trace
            cost_details = {
                "chat": trace_patch.chat_cost,
                "embed": trace_patch.embed_cost,
                "rerank": trace_patch.rerank_cost,
                "total": trace_patch.total_cost,
            }

            spans = []
            if trace_patch.spans:
                spans.extend(trace_patch.spans)

            new_trace = Trace(
                id=trace_id,
                name=trace_patch.name or "Unknown",
                type=trace_patch.type or "unknown",
                status=trace_patch.status or "success",
                channel=trace_patch.channel,
                source=trace_patch.source,
                user_id=trace_patch.user_id,
                start_time=trace_patch.start_time,
                end_time=trace_patch.end_time,
                latency=get_duration(trace_patch.start_time, trace_patch.end_time),
                cost_details=cost_details,
                extra_data=_serialize_for_json(trace_patch.extra_data),
                spans=spans,
            )
            session.add(new_trace)

    def _upsert_metrics_sync(self, session, metric_id: str, patch: dict):
        """Synchronous version of _upsert_metrics."""
        # Filter out None values and serialize JSON fields
        patch = {k: v for k, v in patch.items() if v is not None}
        cost = patch.pop("cost", 0.0)

        # Serialize JSON fields
        json_fields = ["conversation_data", "extra_data"]
        for field in json_fields:
            if field in patch:
                patch[field] = _serialize_for_json(patch[field])

        # Check if metric exists
        existing_metric = session.execute(
            select(Metric).where(Metric.id == metric_id)
        ).scalar_one_or_none()

        if existing_metric:
            # Update existing metric
            update_values = {}
            for key, value in patch.items():
                if hasattr(Metric, key):
                    update_values[key] = value

            # Update cost
            if cost != 0.0:
                update_values["cost"] = (existing_metric.cost or 0.0) + cost

            if update_values:
                session.execute(
                    update(Metric).where(Metric.id == metric_id).values(**update_values)
                )
        else:
            # Create new metric
            metric_data = {"id": metric_id, "cost": cost}
            for key, value in patch.items():
                if hasattr(Metric, key):
                    metric_data[key] = value

            new_metric = Metric(**metric_data)
            session.add(new_metric)

    def shutdown(self) -> None:
        """Clean up resources."""
        if self._engine:
            self._engine.dispose()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def _get_error_message(span: ReadableSpan) -> str:
    for event in span.events:
        if event.name == "exception" and event.attributes:
            return (
                str(event.attributes.get("exception.message"))
                + "\n"
                + str(event.attributes.get("exception.stacktrace"))
            )

    return ""
