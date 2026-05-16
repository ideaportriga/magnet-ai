import asyncio
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from logging import getLogger
from typing import Any, Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.trace import format_span_id
from opentelemetry.trace.status import StatusCode
from litestar.serialization import decode_json
from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config.base import json_serializer_for_sqlalchemy
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


def _get_async_database_url(db_settings: Any) -> str:
    """Return a SQLAlchemy async URL for span export."""
    database_url = db_settings.effective_url
    if not database_url:
        raise ValueError(
            "Database URL is empty. Set DATABASE_URL or configure DB_TYPE/DB_HOST/DB_NAME."
        )

    driver_replacements = {
        "postgresql://": "postgresql+asyncpg://",
        "postgres://": "postgresql+asyncpg://",
        "postgresql+psycopg2://": "postgresql+asyncpg://",
        "mysql://": "mysql+aiomysql://",
        "mysql+pymysql://": "mysql+aiomysql://",
        "sqlite://": "sqlite+aiosqlite://",
        "oracle+cx_oracle://": "oracle+oracledb://",
    }
    for sync_driver, async_driver in driver_replacements.items():
        if database_url.startswith(sync_driver):
            return database_url.replace(sync_driver, async_driver, 1)

    return database_url


def _filter_new_spans(
    existing_spans: list[dict[str, Any]], candidate_spans: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    existing_span_ids = {
        span.get("id") for span in existing_spans if isinstance(span, dict)
    }
    return [
        span
        for span in candidate_spans
        if not isinstance(span, dict) or span.get("id") not in existing_span_ids
    ]


def _get_costs_from_spans(spans: list[dict[str, Any]]) -> dict[str, float]:
    costs = {"chat": 0.0, "embed": 0.0, "rerank": 0.0, "total": 0.0}
    for span in spans:
        if not isinstance(span, dict):
            continue

        cost_details = span.get("cost_details") or {}
        span_cost = (cost_details.get("total") if cost_details else None) or 0.0
        span_type = span.get("type")
        span_type_value = getattr(span_type, "value", span_type)

        if span_type_value == SpanType.CHAT_COMPLETION.value:
            costs["chat"] += span_cost
        elif span_type_value == SpanType.EMBEDDING.value:
            costs["embed"] += span_cost
        elif span_type_value == SpanType.RERANKING.value:
            costs["rerank"] += span_cost

        costs["total"] += span_cost

    return costs


def _sanitize_json_data(obj: Any) -> Any:
    """
    Recursively remove null bytes and control characters from strings.
    These characters cause issues in most SQL databases (especially PostgreSQL JSONB).
    Pattern adapted from data_sync/utils.py clean_text function.
    """
    if isinstance(obj, str):
        # Remove invalid or garbage characters (from clean_text)
        text = obj.replace("\u0e00", " ")
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]", " ", text)
        text = re.sub(r"[\uf020-\uf074\ufffe]", " ", text)
        return text
    elif isinstance(obj, dict):
        return {key: _sanitize_json_data(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_json_data(item) for item in obj]
    else:
        return obj


def _to_datetime(dt: Any) -> datetime | None:
    """Convert any datetime-like object to datetime."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if isinstance(dt, str):
        try:
            # Handle ISO format with Z
            dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return dt_obj if dt_obj.tzinfo else dt_obj.replace(tzinfo=timezone.utc)
        except ValueError as e:
            logger.warning(f"Failed to parse datetime string: {dt}. Error: {e}")
            return None
    # Handle advanced_alchemy DateTimeUTC type
    if hasattr(dt, "replace") and hasattr(dt, "year"):
        return dt if getattr(dt, "tzinfo", None) else dt.replace(tzinfo=timezone.utc)

    logger.warning(f"Unknown datetime type: {type(dt)} for value {dt}")
    return None


def _safe_min_datetime(dt1: Any, dt2: datetime | None) -> datetime | None:
    """Safely compare two datetime objects."""
    dt1_converted = _to_datetime(dt1)
    dt2_converted = _to_datetime(dt2)

    if dt1_converted is None:
        return dt2_converted
    if dt2_converted is None:
        return dt1_converted
    return min(dt1_converted, dt2_converted)


def _safe_max_datetime(dt1: Any, dt2: datetime | None) -> datetime | None:
    """Safely compare two datetime objects."""
    dt1_converted = _to_datetime(dt1)
    dt2_converted = _to_datetime(dt2)

    if dt1_converted is None:
        return dt2_converted
    if dt2_converted is None:
        return dt1_converted
    return max(dt1_converted, dt2_converted)


def _safe_max_span_time(span_time: Any) -> datetime | None:
    """Safely extract datetime from span data."""
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


class SqlAlchemySpanExporter(SpanExporter):
    def __init__(self):
        pass

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        logger.info(f"Exporting {len(spans)} spans")
        start_time = time.time()

        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, schedule the task in background
                # and return immediately (fire-and-forget)
                task = loop.create_task(self._export_spans_isolated(spans))

                # Add error handling callback
                def handle_task_result(task_future):
                    try:
                        task_future.result()
                        end_time = time.time()
                        logger.info(
                            f"Exported {len(spans)} spans in {end_time - start_time} seconds"
                        )
                    except Exception as e:
                        logger.error(f"Background span export failed: {e}")
                        traceback.print_exc()

                task.add_done_callback(handle_task_result)

                # Return success immediately for async context
                return SpanExportResult.SUCCESS

            except RuntimeError:
                # No event loop running, fall back to synchronous exporter approach
                logger.info("No event loop found, falling back to sync export")
                from .sqlalchemy_sync_span_exporter import SqlAlchemySyncSpanExporter

                sync_exporter = SqlAlchemySyncSpanExporter()
                return sync_exporter.export(spans)

        except Exception as e:
            logger.error(f"Unexpected error during span export: {e}")
            traceback.print_exc()
            return SpanExportResult.FAILURE

    async def _export_spans_isolated(self, spans: Sequence[ReadableSpan]):
        """Export spans in the current async context."""
        from core.config.app import settings

        # Use a separate engine instance for span export to avoid conflicts
        # with the main application's database connections
        engine = create_async_engine(
            url=_get_async_database_url(settings.db),
            future=True,
            json_serializer=json_serializer_for_sqlalchemy,
            json_deserializer=decode_json,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,  # Smaller pool for background operations
            echo=False,
        )

        async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        try:
            async with async_session_factory() as session:
                try:
                    trace_accumulator: TraceAccumulator = {}
                    analytics_accumulator: AnalyticsAccumulator = {}

                    for span in spans:
                        # print(span.to_json())
                        await self._export_span(
                            span, trace_accumulator, analytics_accumulator
                        )

                    for trace_id, trace_patch in trace_accumulator.items():
                        await self._upsert_trace(
                            session, trace_id=trace_id, trace_patch=trace_patch
                        )

                    for analytics_id, analytics_patch in analytics_accumulator.items():
                        await self._upsert_metrics(
                            session, analytics_id, analytics_patch
                        )

                    await session.commit()
                except Exception:
                    logger.error("Failed to export spans")
                    traceback.print_exc()
                    await session.rollback()
                    raise
        finally:
            # Clean up the engine
            await engine.dispose()

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
        # Propagate error status: once any span is an error, trace is an error
        if span_status == "error":
            trace.status = "error"
        trace.channel = trace.channel or global_fields.channel.value
        trace.source = trace.source or global_fields.source.value
        # TODO: merge extra data
        trace.extra_data = trace.extra_data or _sanitize_json_data(
            trace_fields.extra_data.value
        )
        trace.user_id = trace.user_id or global_fields.user_id.value

        if (
            config.span_export_method.value
            != SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
            or span_status == "error"
        ):
            trace.spans.append(
                _sanitize_json_data(
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

            # Prepare conversation data
            conversation_data = {}
            for key, value in (conversation.data.value or {}).items():
                conversation_data[key] = value

            # Prepare extra data
            full_extra_data = {
                "input": input,
                "output": output,
                "model_details": model_details,
                "usage_details": usage_details,
                "cost_details": cost_details,
            }
            for key, value in (extra_data or {}).items():
                full_extra_data[key] = value

            x_attributes = dict(global_fields.x_attributes.value or {}) or None

            # Calculate min start_time and max end_time
            current_start = analytics.get("start_time")
            current_end = analytics.get("end_time")

            new_start = span_start_time
            new_end = span_end_time

            if current_start:
                new_start = _safe_min_datetime(current_start, span_start_time)

            if current_end:
                new_end = _safe_max_datetime(current_end, span_end_time)

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
                    "start_time": new_start,
                    "end_time": new_end,
                    "latency": get_duration(new_start, new_end),
                    "conversation_id": conversation.id.value,
                    "conversation_data": conversation_data,
                    "extra_data": full_extra_data,
                    "x_attributes": x_attributes,
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

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    async def _upsert_trace(
        self, session: AsyncSession, trace_id: str, trace_patch: TraceToSave
    ):
        # Slim metadata SELECT: deliberately excludes the `spans` JSONB column.
        # Reading `spans` round-trips an unbounded blob that grows with every
        # export batch, which causes Postgres `printtup` OOM on long traces.
        meta_row = (
            await session.execute(
                select(
                    Trace.name,
                    Trace.type,
                    Trace.status,
                    Trace.channel,
                    Trace.source,
                    Trace.user_id,
                    Trace.start_time,
                    Trace.end_time,
                    Trace.extra_data,
                ).where(Trace.id == trace_id)
            )
        ).one_or_none()

        if meta_row is not None:
            await self._update_existing_trace(session, trace_id, trace_patch, meta_row)
            return

        # Create new trace
        cost_details = {
            "chat": trace_patch.chat_cost,
            "embed": trace_patch.embed_cost,
            "rerank": trace_patch.rerank_cost,
            "total": trace_patch.total_cost,
        }

        spans = list(trace_patch.spans) if trace_patch.spans else []

        trace_values = {
            "id": trace_id,
            "name": trace_patch.name or "Unknown",
            "type": trace_patch.type or "unknown",
            "status": trace_patch.status or "success",
            "channel": trace_patch.channel,
            "source": trace_patch.source,
            "user_id": trace_patch.user_id,
            "start_time": trace_patch.start_time,
            "end_time": trace_patch.end_time,
            "latency": get_duration(trace_patch.start_time, trace_patch.end_time),
            "cost_details": cost_details,
            "extra_data": trace_patch.extra_data,
            "spans": spans,
        }

        if session.get_bind().dialect.name == "postgresql":
            result = await session.execute(
                pg_insert(Trace)
                .values(**trace_values)
                .on_conflict_do_nothing(index_elements=["id"])
            )
            if result.rowcount == 0:
                # Another writer beat us to the insert — merge into the now-existing row.
                meta_row = (
                    await session.execute(
                        select(
                            Trace.name,
                            Trace.type,
                            Trace.status,
                            Trace.channel,
                            Trace.source,
                            Trace.user_id,
                            Trace.start_time,
                            Trace.end_time,
                            Trace.extra_data,
                        ).where(Trace.id == trace_id)
                    )
                ).one_or_none()
                if meta_row is not None:
                    await self._update_existing_trace(
                        session, trace_id, trace_patch, meta_row
                    )
            return

        session.add(Trace(**trace_values))

    async def _update_existing_trace(
        self,
        session: AsyncSession,
        trace_id: str,
        trace_patch: TraceToSave,
        meta_row: Any,
    ):
        # Dedup candidate spans by ID server-side so we never read the full
        # `spans` blob over the wire.
        candidate_ids = [
            s.get("id")
            for s in trace_patch.spans
            if isinstance(s, dict) and s.get("id")
        ]
        existing_ids: set[str] = set()
        if candidate_ids:
            dupe_result = await session.execute(
                text(
                    "SELECT s->>'id' AS span_id "
                    "FROM traces, jsonb_array_elements(spans) s "
                    "WHERE traces.id = :trace_id "
                    "AND s->>'id' = ANY(CAST(:ids AS text[]))"
                ),
                {"trace_id": trace_id, "ids": candidate_ids},
            )
            existing_ids = {row[0] for row in dupe_result if row[0] is not None}

        trace_spans_to_add = [
            s
            for s in trace_patch.spans
            if not isinstance(s, dict) or s.get("id") not in existing_ids
        ]

        new_spans: list[dict[str, Any]] = []

        # Idle-span detection: ask Postgres for the latest end_time among
        # existing root-parented spans rather than scanning the JSONB in Python.
        if trace_patch.root_span and trace_spans_to_add:
            anchor_result = await session.execute(
                text(
                    "SELECT max((s->>'end_time')::timestamptz) "
                    "FROM traces, jsonb_array_elements(spans) s "
                    "WHERE traces.id = :trace_id "
                    "AND s->>'parent_id' = :trace_id"
                ),
                {"trace_id": trace_id},
            )
            latest_existing_root_span_end_time = anchor_result.scalar()

            if latest_existing_root_span_end_time:
                latest_existing_root_span_end_time = apply_utc_timezone(
                    latest_existing_root_span_end_time
                )
                root_span_start_time = _safe_max_span_time(
                    trace_patch.root_span.get("start_time")
                )
                idle_span = {
                    "id": format_span_id(RandomIdGenerator().generate_span_id()),
                    "parent_id": trace_id,
                    "type": "idle",
                    "start_time": latest_existing_root_span_end_time,
                    "end_time": root_span_start_time,
                    "latency": get_duration(
                        latest_existing_root_span_end_time,
                        root_span_start_time,
                    ),
                }
                new_spans.append(idle_span)

        new_spans.extend(trace_spans_to_add)

        costs_to_add = (
            {
                "chat": trace_patch.chat_cost,
                "embed": trace_patch.embed_cost,
                "rerank": trace_patch.rerank_cost,
                "total": trace_patch.total_cost,
            }
            if len(trace_spans_to_add) == len(trace_patch.spans)
            else _get_costs_from_spans(trace_spans_to_add)
        )

        new_status = "error" if trace_patch.status == "error" else meta_row.status

        merged_start = _safe_min_datetime(meta_row.start_time, trace_patch.start_time)
        merged_end = _safe_max_datetime(meta_row.end_time, trace_patch.end_time)
        merged_latency = (
            get_duration(_to_datetime(merged_start), _to_datetime(merged_end))
            if merged_start and merged_end
            else None
        )

        # Build the UPDATE. Append spans server-side via JSONB `||` and roll
        # cost_details forward in-place — `spans` never leaves Postgres.
        new_spans_json = (
            json_serializer_for_sqlalchemy(new_spans) if new_spans else None
        )

        params: dict[str, Any] = {
            "trace_id": trace_id,
            "name": meta_row.name or trace_patch.name,
            "type": meta_row.type or trace_patch.type,
            "status": new_status,
            "channel": meta_row.channel or trace_patch.channel,
            "source": meta_row.source or trace_patch.source,
            "user_id": meta_row.user_id or trace_patch.user_id,
            "start_time": merged_start,
            "end_time": merged_end,
            "latency": merged_latency,
            "chat_cost": costs_to_add["chat"],
            "embed_cost": costs_to_add["embed"],
            "rerank_cost": costs_to_add["rerank"],
            "total_cost": costs_to_add["total"],
        }

        set_clauses = [
            "name = :name",
            "type = :type",
            "status = :status",
            "channel = :channel",
            "source = :source",
            "user_id = :user_id",
            "start_time = :start_time",
            "end_time = :end_time",
            "latency = :latency",
            "cost_details = jsonb_build_object("
            "'chat', COALESCE((cost_details->>'chat')::float8, 0) + :chat_cost, "
            "'embed', COALESCE((cost_details->>'embed')::float8, 0) + :embed_cost, "
            "'rerank', COALESCE((cost_details->>'rerank')::float8, 0) + :rerank_cost, "
            "'total', COALESCE((cost_details->>'total')::float8, 0) + :total_cost)",
        ]

        if meta_row.extra_data is None and trace_patch.extra_data is not None:
            set_clauses.append("extra_data = CAST(:extra_data AS jsonb)")
            params["extra_data"] = json_serializer_for_sqlalchemy(
                trace_patch.extra_data
            )

        if new_spans_json is not None:
            set_clauses.append(
                "spans = COALESCE(spans, '[]'::jsonb) || CAST(:new_spans AS jsonb)"
            )
            params["new_spans"] = new_spans_json

        await session.execute(
            text(f"UPDATE traces SET {', '.join(set_clauses)} WHERE id = :trace_id"),
            params,
        )

    async def _upsert_metrics(self, session: AsyncSession, metric_id: str, patch: dict):
        # Filter out None values
        patch = {k: v for k, v in patch.items() if v is not None}
        cost = patch.pop("cost", 0.0)

        # Check if metric exists
        result = await session.execute(select(Metric).where(Metric.id == metric_id))
        existing_metric = result.scalar_one_or_none()

        if existing_metric:
            # Update existing metric
            update_values = {}

            # Handle start_time and end_time specifically
            if "start_time" in patch:
                start_time = patch.pop("start_time")
                update_values["start_time"] = _safe_min_datetime(
                    existing_metric.start_time, start_time
                )

            if "end_time" in patch:
                end_time = patch.pop("end_time")
                update_values["end_time"] = _safe_max_datetime(
                    existing_metric.end_time, end_time
                )

            for key, value in patch.items():
                if hasattr(Metric, key):
                    update_values[key] = value

            # Update cost
            if cost != 0.0:
                update_values["cost"] = (existing_metric.cost or 0.0) + cost

            # Recalculate latency if start and end times are available
            start = _to_datetime(
                update_values.get("start_time", existing_metric.start_time)
            )
            end = _to_datetime(update_values.get("end_time", existing_metric.end_time))

            if start and end:
                update_values["latency"] = get_duration(start, end)

            if update_values:
                await session.execute(
                    update(Metric).where(Metric.id == metric_id).values(**update_values)
                )
        else:
            # Create new metric
            metric_data = {"id": metric_id, "cost": cost}
            for key, value in patch.items():
                if hasattr(Metric, key):
                    metric_data[key] = value

            if session.get_bind().dialect.name == "postgresql":
                result = await session.execute(
                    pg_insert(Metric)
                    .values(**metric_data)
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                if result.rowcount == 0:
                    await self._upsert_metrics(
                        session, metric_id, patch | {"cost": cost}
                    )
                return

            session.add(Metric(**metric_data))


def _get_error_message(span: ReadableSpan) -> str:
    for event in span.events:
        if event.name == "exception" and event.attributes:
            return (
                str(event.attributes.get("exception.message"))
                + "\n"
                + str(event.attributes.get("exception.stacktrace"))
            )

    return ""
