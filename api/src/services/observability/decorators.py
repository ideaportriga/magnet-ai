import asyncio
import traceback
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, Tuple, TypeVar, Unpack, cast, overload

from litestar import route as LitestarRouteHandler
from opentelemetry import baggage, context
from opentelemetry import trace as otel_trace
from opentelemetry.context.context import Context
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.trace import INVALID_SPAN, Span, SpanContext, SpanKind
from opentelemetry.trace.status import StatusCode

from services.observability.models import (
    BaggageParams,
    CostDetails,
    DecoratorParams,
    LLMType,
    ObservabilityConfig,
    ObservationModelDetails,
    ObservedConversation,
    ObservedFeature,
    ObservedFeatureInstance,
    ObservedGlobals,
    SpanExportMethod,
    SpanFields,
    SpanParams,
    SpanType,
    TraceObservabilityFields,
    TraceParams,
    UsageDetails,
)
from services.observability.otel import OtelMetric, OtelTokenType
from services.observability.otel.attributes import (
    create_otel_metric_attributes,
    create_otel_span_attributes,
)
from services.observability.otel.config import (
    gen_ai_cost_histogram,
    gen_ai_duration_histogram,
    gen_ai_usage_histogram,
    magnet_ai_feature_duration_histogram,
    otel_tracer,
)
from services.observability.utils import (
    extract_x_attributes_from_request,
    get_duration,
    get_timestamp,
    merge_dicts,
)

logger = getLogger(__name__)


_root_span: ContextVar[Span | None] = ContextVar("root_span", default=None)

T = TypeVar("T", bound=Callable[..., Any] | LitestarRouteHandler)


class ObservabilityContext:
    @overload
    def observe(self, func_or_route: T, /) -> T: ...

    @overload
    def observe(
        self, func_or_route: None = None, /, **params: Unpack[DecoratorParams]
    ) -> Callable[[T], T]: ...

    def observe(
        self, func_or_route: T | None = None, /, **params: Unpack[DecoratorParams]
    ) -> T | Callable[[T], T]:
        """Wrap a function to create and manage tracing around its execution, supporting both synchronous and asynchronous functions. It captures the function's execution context.
        In case of an exception, the observation is updated with error details.

        Span-specific parameters:
            enabled (bool): If True, the decorator is enabled. Default is True.
            name (Optional[str]): Name of the created observation. Overwrites the function name as the default used for the observation name.
            type (Optional[str]): Type of the created observation.
            description (Optional[str]): User friendly description of the observation.
            channel (Optional[str]): Channel of the observation. Can be any string.
            source (Optional[str]): Source of the observation. Can be any string.
            extra_data (Optional[Any]): Additional data of the observation. Can be any JSON object. This data is merged.
            capture_input (bool): If True, captures the args and kwargs of the function as input. Default is False.
            capture_output (bool): If True, captures the return value of the function as output. Default is False.

        Trace-specific parameters:
            trace_enabled (bool): If True, the trace is enabled. Default is True.
            trace_name (Optional[str]): Name of the trace. If omitted, it will be set to the name of the span.

        Returns:
            Callable: A wrapped version of the original function that, upon execution, is automatically observed.

        Raises:
            Exception: Propagates exceptions from the wrapped function after logging and updating the observation with error details.

        """

        def decorator(func_or_route: T) -> T:
            # If decorator wraps Litestar route handler
            if isinstance(func_or_route, LitestarRouteHandler):
                if asyncio.iscoroutinefunction(func_or_route._fn):
                    return cast(
                        T, self._observe_async_litestar(func_or_route, **params)
                    )
                return cast(T, self._observe_sync_litestar(func_or_route, **params))

            # If decorator wraps an async function
            if asyncio.iscoroutinefunction(func_or_route):
                return cast(T, self.observe_async(func_or_route, **params))

            # For all other cases
            return cast(T, self.observe_sync(func_or_route, **params))

        """Handle decorator with or without parentheses.
        
        This logic enables the decorator to work both with and without parentheses:
        - @observe - Python passes the function directly to the decorator
        - @observe() - Python calls the decorator first, which must return a function decorator
        
        When called without arguments (@observe), the func parameter contains the function to decorate,
        so we directly apply the decorator to it. When called with parentheses (@observe()), 
        func is None, so we return the decorator function itself for Python to apply in the next step.
        """

        if func_or_route is None:
            return decorator

        return decorator(func_or_route)

    # region Decorator wrapper methods

    def _observe_async_litestar(
        self, route: LitestarRouteHandler, /, **params: Unpack[DecoratorParams]
    ) -> LitestarRouteHandler:
        func = route._fn

        @wraps(func)
        async def async_wrapper(*func_args, **func_kwargs):
            (trace_id, prepared_func_kwargs, prepared_decor_params, x_attributes) = (
                self._prepare_params(
                    func.__name__, func_args, func_kwargs, params, True
                )
            )

            if not prepared_decor_params.get("enabled"):
                return await func(*func_args, **prepared_func_kwargs)

            result = None

            _, baggage_token, otel_span, otel_token = self._before_call_handler(
                func.__name__,
                func_args,
                prepared_func_kwargs,
                trace_id,
                x_attributes=x_attributes,
                **prepared_decor_params,
            )

            try:
                result = await func(*func_args, **prepared_func_kwargs)
            except Exception as e:
                self._handle_exception(otel_span, e)
            finally:
                self._after_call_handler(
                    baggage_token,
                    otel_span,
                    otel_token,
                    result,
                    **prepared_decor_params,
                )

                if result is not None:
                    return result

        route._fn = cast(Callable, async_wrapper)
        return route

    def _observe_sync_litestar(
        self, route: LitestarRouteHandler, /, **params: Unpack[DecoratorParams]
    ) -> LitestarRouteHandler:
        func = route._fn

        @wraps(func)
        def sync_wrapper(*func_args, **func_kwargs):
            (trace_id, final_cleaned_kwargs, prepared_decor_params, x_attributes) = (
                self._prepare_params(
                    func.__name__, func_args, func_kwargs, params, True
                )
            )

            if not prepared_decor_params.get("enabled", True):
                return func(*func_args, **final_cleaned_kwargs)

            result = None

            _, baggage_token, otel_span, otel_token = self._before_call_handler(
                func.__name__,
                func_args,
                final_cleaned_kwargs,
                trace_id,
                x_attributes=x_attributes,
                **prepared_decor_params,
            )

            try:
                result = func(*func_args, **final_cleaned_kwargs)
            except Exception as e:
                self._handle_exception(otel_span, e)
            finally:
                self._after_call_handler(
                    baggage_token,
                    otel_span,
                    otel_token,
                    result,
                    **prepared_decor_params,
                )

                if result is not None:
                    return result

        route._fn = cast(Callable, sync_wrapper)
        return route

    def observe_async(
        self, func: Callable[..., Any], /, **params: Unpack[DecoratorParams]
    ) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*func_args, **func_kwargs):
            (trace_id, final_cleaned_kwargs, prepared_decor_params, _) = (
                self._prepare_params(func.__name__, func_args, func_kwargs, params)
            )

            if not prepared_decor_params.get("enabled", True):
                return await func(*func_args, **final_cleaned_kwargs)

            result = None

            _, baggage_token, otel_span, otel_token = self._before_call_handler(
                func.__name__,
                func_args,
                final_cleaned_kwargs,
                trace_id,
                **prepared_decor_params,
            )

            try:
                result = await func(*func_args, **final_cleaned_kwargs)
            except Exception as e:
                self._handle_exception(otel_span, e)
            finally:
                self._after_call_handler(
                    baggage_token,
                    otel_span,
                    otel_token,
                    result,
                    **prepared_decor_params,
                )

                if result is not None:
                    return result

        return async_wrapper

    def observe_sync(
        self, func: Callable[..., Any], /, **params: Unpack[DecoratorParams]
    ) -> Callable[..., Any]:
        @wraps(func)
        def sync_wrapper(*func_args, **func_kwargs):
            (trace_id, final_cleaned_kwargs, prepared_decor_params, _) = (
                self._prepare_params(func.__name__, func_args, func_kwargs, params)
            )

            if not prepared_decor_params.get("enabled", True):
                return func(*func_args, **final_cleaned_kwargs)

            result = None

            _, baggage_token, otel_span, otel_token = self._before_call_handler(
                func.__name__,
                func_args,
                final_cleaned_kwargs,
                trace_id,
                **prepared_decor_params,
            )

            try:
                result = func(*func_args, **final_cleaned_kwargs)
            except Exception as e:
                self._handle_exception(otel_span, e)
            finally:
                self._after_call_handler(
                    baggage_token,
                    otel_span,
                    otel_token,
                    result,
                    **prepared_decor_params,
                )

                if result is not None:
                    return result

        return sync_wrapper

    @contextmanager
    def observe_feature(self, feature: ObservedFeature, instance_id: str | None = None):
        # TODO: make this cleaner
        _, _, prepared_decor_params, _ = self._prepare_params("monitor_feature_usage")
        prepared_decor_params["type"] = feature.type.value.span_type

        start_time, baggage_token, otel_span, otel_token = self._before_call_handler(
            "monitor_feature_usage", **prepared_decor_params
        )

        # Prepare feature instances
        feature_instance = ObservedFeatureInstance(feature, instance_id)
        parent_features = [
            value
            for key, value in baggage.get_all().items()
            if key.startswith("feature.") and isinstance(value, ObservedFeatureInstance)
        ]

        # Update span attributes with feature and parent features
        if otel_span:
            otel_span.set_attributes(
                create_otel_span_attributes(
                    feature=feature_instance, parent_features=parent_features
                )
            )

        # Update baggage with the newly added feature
        ctx = baggage.set_baggage(f"feature.{feature.type.otel_name}", feature_instance)
        context.attach(ctx)

        # Execute code block and catch errors if any
        try:
            yield feature_instance.id.value
        except Exception as e:
            self._handle_exception(otel_span, e)
        finally:
            # Prepare global fields
            global_fields = ObservedGlobals.from_otel_baggage(baggage.get_all())

            end_time = self._after_call_handler(
                baggage_token, otel_span, otel_token, None, **prepared_decor_params
            )

            # Record Magnet AI metrics
            magnet_ai_feature_duration_histogram.record(
                get_duration(start_time, end_time) or 0,
                create_otel_metric_attributes(
                    OtelMetric.MAGNET_AI_FEATURE_DURATION,
                    feature,
                    global_fields=global_fields,
                ),
            )

    # endregion

    def _prepare_params(
        self,
        func_name: str,
        func_args: Tuple = (),
        func_kwargs: Dict = {},
        decor_params: DecoratorParams = {},
        handle_litestar_params: bool = False,
        /,
    ):
        # Prepare observed function kwargs
        prepared_func_kwargs = func_kwargs.copy()
        observability_overrides = dict(
            prepared_func_kwargs.pop("_observability_overrides", {})
        )
        decor_overrides = dict(observability_overrides.get("decorator", {}))

        # Prepare observation decorator params
        # Since Unpack and TypeDict support only None value as default, other default values must be assigned manually
        prepared_decor_params = decor_params.copy()
        prepared_decor_params["enabled"] = decor_params.get("enabled", True)
        prepared_decor_params["trace_enabled"] = decor_params.get("trace_enabled", True)

        # Override decorator params with values from special _observability_overrides key
        for key, value in decor_overrides.items():
            prepared_decor_params[key] = value

        if handle_litestar_params:
            # TODO: current hack to pass trace_id  from request to the decorator, needs to be refactored
            trace_id = func_kwargs.get(
                "trace_id", observability_overrides.get("trace_id")
            )
            x_attributes = extract_x_attributes_from_request(func_args, func_kwargs)
        else:
            trace_id = observability_overrides.get("trace_id")
            x_attributes = None

        return (
            trace_id,
            prepared_func_kwargs,
            prepared_decor_params,
            x_attributes,
        )

    def _before_call_handler(
        self,
        func_name: str,
        func_args: Tuple = (),
        func_kwargs: Dict = {},
        trace_id: str | None = None,
        /,
        x_attributes: Dict[str, Any] | None = None,
        **params: Unpack[DecoratorParams],
    ) -> tuple[datetime, Token[Context] | None, Span | None, Token[Context] | None]:
        # Get start time as early as possible
        start_time = get_timestamp()

        # Check if new trace is started
        new_trace_started = not context.get_current()

        # Initialize baggage if current context is empty (fresh trace is started)
        baggage_token = None
        if new_trace_started:
            ctx = baggage.set_baggage("channel", params.get("channel"))
            ctx = baggage.set_baggage("source", params.get("source"), ctx)
            ctx = baggage.set_baggage("consumer_type", params.get("consumer_type"), ctx)
            ctx = baggage.set_baggage("consumer_name", params.get("consumer_name"), ctx)
            ctx = baggage.set_baggage("user_id", params.get("user_id"), ctx)
            ctx = baggage.set_baggage("x_attributes", x_attributes, ctx)
            baggage_token = context.attach(ctx)

        # Prepare span
        otel_span, otel_token = self._start_tracing(
            func_name, func_args, func_kwargs, trace_id, start_time, **params
        )

        return start_time, baggage_token, otel_span, otel_token

    # region Start tracing recording
    def _start_tracing(
        self,
        func_name: str,
        func_args: Tuple = (),
        func_kwargs: Dict = {},
        trace_id: str | None = None,
        start_time: datetime = get_timestamp(),
        /,
        **params: Unpack[DecoratorParams],
    ) -> tuple[Span | None, Token[Context] | None]:
        if not (params.get("enabled") and params.get("trace_enabled")):
            return None, None

        try:
            span_name = params.get("name") or func_name
            span_type = params.get("type") or SpanType.SPAN
            extra_data = params.get("extra_data") or {}

            # Get current span
            current_otel_span = otel_trace.get_current_span()
            ctx = context.get_current()

            if current_otel_span is not INVALID_SPAN and trace_id:
                logger.warning(
                    "Provided trace id, but parent exists. Ignoring provided trace id."
                )
            elif trace_id:
                span_context = SpanContext(
                    trace_id=int(trace_id, 16),
                    span_id=RandomIdGenerator().generate_span_id(),
                    trace_flags=otel_trace.TraceFlags(0x01),  # Mark span as sampled
                    is_remote=False,  # This span is created locally
                )
                ctx = otel_trace.set_span_in_context(
                    otel_trace.NonRecordingSpan(span_context)
                )
                context.attach(ctx)  # TODO: deatch token later

            # Prepare global fields
            global_fields = ObservedGlobals(
                channel=params.get("channel"),
                source=params.get("source"),
                consumer_type=params.get("consumer_type"),
                consumer_name=params.get("consumer_name"),
                user_id=params.get("user_id"),
            )

            # Capture input if required
            input = func_kwargs if params.get("capture_input") else None

            # Prepare span fields
            span_fields = SpanFields(
                name=span_name,
                type=span_type or SpanType.SPAN,
                start_time=start_time,
                description=params.get("description"),
                extra_data=extra_data,
                input=input,
            )

            match span_type:
                case SpanType.CHAT_COMPLETION:
                    otel_name = "chat"
                    otel_kind = SpanKind.CLIENT
                case SpanType.EMBEDDING:
                    otel_name = "embeddings"
                    otel_kind = SpanKind.CLIENT
                case SpanType.RERANKING:
                    otel_name = "reranker"
                    otel_kind = SpanKind.CLIENT
                case _:
                    otel_name = span_name
                    otel_kind = SpanKind.INTERNAL

            if _root_span.get():
                trace_fields = self._get_current_trace_fields()
            else:
                otel_name = "root"
                trace_fields = TraceObservabilityFields(
                    name=params.get("trace_name") or span_fields.name,
                    extra_data=extra_data,
                )

            otel_span = otel_tracer.start_span(
                name=otel_name,
                kind=otel_kind,
                start_time=int(start_time.timestamp() * 1_000_000_000),
                attributes=create_otel_span_attributes(
                    global_fields=global_fields,
                    trace_fields=trace_fields,
                    span_fields=span_fields,
                ),
            )

            # Create current span as root if it's a first span in the trace
            if _root_span.get() is None:
                _root_span.set(otel_span)

            ctx = otel_trace.set_span_in_context(otel_span, ctx)
            otel_token = context.attach(ctx)

            return otel_span, otel_token
        except Exception:
            logger.error("Failed to start tracing before function call")
            traceback.print_exc()
            return None, None

    # endregion

    def _after_call_handler(
        self,
        baggage_token: Token[Context] | None,
        otel_span: Span | None,
        otel_token: Token[Context] | None,
        result: Any,
        /,
        **params: Unpack[DecoratorParams],
    ) -> datetime:
        if otel_span and otel_token:
            self._end_tracing(otel_span, otel_token, result, **params)

        # Detach baggage to avoid context leakage
        if baggage_token:
            context.detach(baggage_token)

        return get_timestamp()

    def _end_tracing(
        self,
        otel_span: Span,
        otel_token: Token[Context],
        result: Any,
        /,
        **params: Unpack[DecoratorParams],
    ):
        try:
            output = result if params.get("capture_output") else None

            otel_span.set_attributes(
                create_otel_span_attributes(
                    observability_config=ObservabilityConfig.from_otel_baggage(
                        baggage.get_all(),
                    ),
                    global_fields=ObservedGlobals.from_otel_baggage(
                        baggage.get_all(),
                    ),
                    span_fields=SpanFields(output=output),
                    conversation=ObservedConversation.from_otel_baggage(
                        baggage.get_all(),
                    ),
                )
            )

            otel_span.end()
            context.detach(otel_token)

            # If last observation is a trace, we need to check whethere it's the last trace or not
            readable_span = cast(ReadableSpan, otel_span)
            if readable_span.name == "root":
                _root_span.set(None)

        except Exception as e:
            logger.error(f"Failed to finalize tracing after function call: {e}")

    def _handle_exception(self, span: Span | None, e: Exception, /):
        if span:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR)
        raise e

    def update_current_config(
        self, *, span_export_method: SpanExportMethod | None = None
    ):
        ctx = context.get_current()
        ctx = baggage.set_baggage(
            "config.span_export_method", span_export_method, context=ctx
        )
        context.attach(ctx)

    # TODO: rename this to something else
    def update_current_baggage(self, /, **kwargs: Unpack[BaggageParams]):
        ctx = context.get_current()
        for key, value in kwargs.items():
            if key == "extra_data":
                data = baggage.get_baggage("extra_data", ctx)
                data = cast(dict[str, Any], data) if data else {}
                data_patch = cast(dict[str, Any], value) if value else {}
                merged_data = merge_dicts(data, data_patch)
                ctx = baggage.set_baggage("extra_data", merged_data, context=ctx)
            elif key == "conversation_id":
                ctx = baggage.set_baggage("conversation.id", value, context=ctx)
            elif key == "conversation_data":
                data = baggage.get_baggage("conversation.data", ctx)
                data = cast(dict[str, Any], data) if data else {}
                data_patch = cast(dict[str, Any], value) if value else {}
                merged_data = merge_dicts(data, data_patch)
                ctx = baggage.set_baggage("conversation.data", merged_data, context=ctx)
            else:
                ctx = baggage.set_baggage(key, value, context=ctx)
        context.attach(ctx)

    def _get_current_trace_fields(self) -> TraceObservabilityFields:
        if not _root_span.get():
            logger.warning("No root span found in the current context")
            return TraceObservabilityFields()

        span = cast(ReadableSpan, _root_span.get())
        return TraceObservabilityFields.from_otel_attributes(span.attributes or {})

    def get_current_trace_id(self) -> str | None:
        current_otel_trace_id = (
            otel_trace.get_current_span().get_span_context().trace_id
        )
        if current_otel_trace_id == 0:
            logger.warning("No trace found in the current context")
            return None

        return otel_trace.format_trace_id(current_otel_trace_id)

    def update_current_trace(self, /, **params: Unpack[TraceParams]) -> None:
        root_span = _root_span.get()
        if not root_span:
            logger.warning(
                "No trace found in the current context, skipping trace update"
            )
            return

        global_fields = ObservedGlobals(user_id=params.get("user_id"))
        trace_fields = TraceObservabilityFields(
            name=params.get("name"),
            type=params.get("type"),
            extra_data=params.get("extra_data"),
        )

        root_span.set_attributes(
            create_otel_span_attributes(
                global_fields=global_fields, trace_fields=trace_fields
            )
        )

    def update_current_span(self, /, **params: Unpack[SpanParams]):
        self._update_current_span(SpanFields(**params))

    def _update_current_span(self, fields: SpanFields):
        current_otel_span = otel_trace.get_current_span()
        current_otel_span_context = current_otel_span.get_span_context()
        current_otel_span_id = current_otel_span_context.span_id
        if current_otel_span_id == 0:
            logger.warning("No span found in the current context, skipping span update")
            return

        readable_span = cast(ReadableSpan, current_otel_span)
        if readable_span.attributes:
            fields.type = cast(str, readable_span.attributes.get("magnet_ai.type"))
            current_otel_span.set_attributes(
                create_otel_span_attributes(span_fields=fields)
            )
        else:
            logger.warning(
                "No attributes found in the current span, skipping span update"
            )
            return

    def _update_span_with_llm_response(
        self,
        usage_details: UsageDetails | None,
        cost_details: CostDetails | None,
        output: Any = None,
    ):
        try:
            self._update_current_span(
                SpanFields(
                    usage_details=usage_details,
                    cost_details=cost_details,
                    output=output,
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to update current span with LLM response: {e}")
            traceback.print_exc()

    def record_llm_metrics(
        self,
        *,
        llm_type: LLMType,
        model: ObservationModelDetails,
        duration: float,
        usage: UsageDetails | None = None,
        cost: CostDetails | None = None,
    ):
        gen_ai_duration_histogram.record(
            duration,
            create_otel_metric_attributes(
                OtelMetric.GEN_AI_DURATION,
                llm_type,
                model_details=model,
            ),
        )
        gen_ai_usage_histogram.record(
            usage.input if usage and usage.input else 0,
            create_otel_metric_attributes(
                OtelMetric.GEN_AI_USAGE,
                llm_type,
                model_details=model,
                token_type=OtelTokenType.OUTPUT,
            ),
        )
        gen_ai_usage_histogram.record(
            usage.output if usage and usage.output else 0,
            create_otel_metric_attributes(
                OtelMetric.GEN_AI_USAGE,
                llm_type,
                model_details=model,
                token_type=OtelTokenType.OUTPUT,
            ),
        )
        gen_ai_cost_histogram.record(
            cost.input if cost and cost.input else 0,
            create_otel_metric_attributes(
                OtelMetric.GEN_AI_COST,
                llm_type,
                model_details=model,
                token_type=OtelTokenType.INPUT,
            ),
        )
        gen_ai_cost_histogram.record(
            cost.output if cost and cost.output else 0,
            create_otel_metric_attributes(
                OtelMetric.GEN_AI_COST,
                llm_type,
                model_details=model,
                token_type=OtelTokenType.OUTPUT,
            ),
        )


observability_context = ObservabilityContext()
observe = observability_context.observe
