import json
from logging import getLogger
from typing import Any, Mapping, cast

from opentelemetry.util.types import AttributeValue

from services.observability.models import (
    CostDetails,
    CostInputDetails,
    CostOutputDetails,
    FeatureType,
    ObservabilityConfig,
    ObservationModelDetails,
    ObservedConversation,
    ObservedFeature,
    ObservedFeatureInstance,
    ObservedGlobals,
    ObservedPromptTemplate,
    SpanFields,
    SpanType,
    TraceObservabilityFields,
    UsageDetails,
    UsageInputDetails,
    UsageOutputDetails,
)
from utils.serializer import DefaultMongoDbSerializer

from .utils import clean_attributes, expand_fields

logger = getLogger(__name__)


def create_otel_span_attributes(
    *,
    observability_config: ObservabilityConfig | None = None,
    global_fields: ObservedGlobals | None = None,
    trace_fields: TraceObservabilityFields | None = None,
    span_fields: SpanFields | None = None,
    feature: ObservedFeatureInstance | None = None,
    parent_features: list[ObservedFeatureInstance] | None = None,
    conversation: ObservedConversation | None = None,
) -> Mapping[str, AttributeValue]:
    attributes: Mapping[str, AttributeValue | None] = {}

    # Create MagnetAI config level attributes
    if observability_config:
        attributes.update(observability_config.to_otel_attributes())

    # Create MagnetAI global level attributes
    if global_fields:
        attributes.update(global_fields.to_otel_attributes())

    # Create MagnetAI trace level attributes
    if trace_fields:
        attributes.update(trace_fields.to_otel_attributes())

    # Create MagnetAI span level attributes
    if span_fields:
        attributes.update(_span_magnet_ai_otel_attrs(span_fields))

    # Create MagnetAI feature level attributes
    if feature:
        attributes.update(feature.to_otel_attributes())

    # Create MagnetAI parent feature level attributes
    if parent_features:
        for i, parent_feature in enumerate(parent_features):
            attributes.update(
                parent_feature.to_otel_attributes(
                    prefix=f"magnet_ai.parent_feature.{i}"
                )
            )

    # Create MagnetAI conversation level attributes
    if conversation:
        attributes.update(conversation.to_otel_attributes())

    if span_fields:
        if span_fields.type:
            match span_fields.type:
                case SpanType.CHAT_COMPLETION:
                    attributes.update(_gen_ai_chat_otel_attributes(span_fields))
                case SpanType.EMBEDDING:
                    attributes.update(_gen_ai_embeddings_otel_attributes(span_fields))
                case SpanType.RERANKING:
                    attributes.update(_gen_ai_reranker_otel_attributes(span_fields))

    return clean_attributes(attributes)


def _span_magnet_ai_otel_attrs(fields: SpanFields):
    attributes: Mapping[str, AttributeValue | None] = {}

    model = fields.model or {}
    model_params: dict[str, Any] = model.get("parameters") or {}

    attributes.update(
        expand_fields(
            "magnet_ai",
            fields,
            exclude=[
                "start_time",
                "end_time",
                "status",
                "status_message",
                "prompt_template",
                "model",
                "extra_data",
                "input",
                "output",
                "usage_details",
                "cost_details",
            ],
        )
    )
    attributes.update(
        expand_fields("magnet_ai.prompt_template", fields.prompt_template)
    )
    attributes.update(
        expand_fields(
            "magnet_ai.model", model, exclude=["otel_gen_ai_system", "parameters"]
        )
    )
    attributes.update(
        expand_fields(
            "magnet_ai.model.parameters",
            model_params,
            exclude=["response_format", "tools"],
        )
    )
    attributes["magnet_ai.model.tools"] = (
        json.dumps(model_params.get("tools")) if model_params.get("tools") else None
    )
    attributes.update(
        expand_fields("magnet_ai.extra_data", fields.extra_data, json_dump=True)
    )
    attributes["magnet_ai.input"] = (
        json.dumps(fields.input, cls=DefaultMongoDbSerializer) if fields.input else None
    )
    attributes["magnet_ai.output"] = (
        json.dumps(fields.output, cls=DefaultMongoDbSerializer)
        if fields.output
        else None
    )
    attributes.update(
        expand_fields(
            "magnet_ai.usage_details",
            fields.usage_details,
            exclude=["input_details", "output_details"],
        ),
    )
    attributes.update(
        expand_fields(
            "magnet_ai.usage_details.input_details",
            fields.usage_details.input_details if fields.usage_details else None,
        )
    )
    attributes.update(
        expand_fields(
            "magnet_ai.usage_details.output_details",
            fields.usage_details.output_details if fields.usage_details else None,
        )
    )
    attributes.update(
        expand_fields(
            "magnet_ai.cost_details",
            fields.cost_details,
            exclude=["input_details", "output_details"],
        ),
    )
    attributes.update(
        expand_fields(
            "magnet_ai.cost_details.input_details",
            fields.cost_details.input_details if fields.cost_details else None,
        )
    )
    attributes.update(
        expand_fields(
            "magnet_ai.cost_details.output_details",
            fields.cost_details.output_details if fields.cost_details else None,
        )
    )

    return attributes


def _gen_ai_chat_otel_attributes(fields: SpanFields):
    attributes: Mapping[str, AttributeValue | None] = {}

    model: ObservationModelDetails = fields.model or ObservationModelDetails()
    model_params: dict[str, Any] = model.get("parameters") or {}
    usage_details: UsageDetails = fields.usage_details or UsageDetails()
    cost_details: CostDetails = fields.cost_details or CostDetails()
    output: dict[str, Any] = fields.output or {}

    # Create required attributes by OpenTelemetry Gen AI
    # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/#inference
    attributes["gen_ai.operation.name"] = "chat"
    attributes["gen_ai.system"] = model.get("otel_gen_ai_system")
    attributes["gen_ai.request.model"] = model_params.get("llm")

    # Add conditionally required attributes by OpenTelemetry Gen AI
    attributes["gen_ai.conversation.id"] = fields.conversation_id

    # Add recommended attributes by OpenTelemetry Gen AI
    # TODO: default values for max_tokens, temperature, top_k and top_p should be taken into account
    # attributes["gen_ai.request.frequency_penalty"] = "" # MagnetAI does not support this parameter yet
    attributes["gen_ai.request.max_tokens"] = model_params.get("max_tokens")
    # attributes["gen_ai.request.presence_penalty"] = "" # MagnetAI does not support this parameter yet
    # attributes["gen_ai.request.stop_sequences"] = "" # MagnetAI does not support this parameter yet
    attributes["gen_ai.request.temperature"] = model_params.get("temperature")
    # attributes["gen_ai.request.top_k"] = "" # MagnetAI does not support this parameter yet
    attributes["gen_ai.request.top_p"] = model_params.get("top_p")
    # attributes["gen_ai.response.finish_reasons"] = "" # MagnetAI does not support this parameter yet
    attributes["gen_ai.response.id"] = output.get("id")
    attributes["gen_ai.response.model"] = model_params.get("llm")
    attributes["gen_ai.usage.input_tokens"] = usage_details.input
    attributes["gen_ai.usage.output_tokens"] = usage_details.output

    # Add some popular vendor-specific attributes
    attributes["gen_ai.usage.cost"] = cost_details.total
    attributes["model"] = model_params.get("llm")

    return attributes


def _gen_ai_embeddings_otel_attributes(fields: SpanFields):
    attributes: Mapping[str, AttributeValue | None] = {}

    model: ObservationModelDetails = fields.model or ObservationModelDetails()
    model_params: dict[str, Any] = model.get("parameters") or {}
    usage_details: UsageDetails = fields.usage_details or UsageDetails()

    # Create required attributes by OpenTelemetry Gen AI
    # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/#inference
    attributes["gen_ai.operation.name"] = "embeddings"
    attributes["gen_ai.system"] = model.get("otel_gen_ai_system")
    attributes["gen_ai.request.model"] = model_params.get("llm")

    # Add recommended attributes by OpenTelemetry Gen AI
    attributes["gen_ai.request.encoding_formats"] = ["float"]
    attributes["gen_ai.usage.input_tokens"] = usage_details.input

    return attributes


def _gen_ai_reranker_otel_attributes(fields: SpanFields):
    attributes: Mapping[str, AttributeValue | None] = {}

    model: ObservationModelDetails = fields.model or ObservationModelDetails()
    model_params: dict[str, Any] = model.get("parameters") or {}
    usage_details: UsageDetails = fields.usage_details or UsageDetails()

    # Create required attributes by OpenTelemetry Gen AI
    # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/#inference
    attributes["gen_ai.operation.name"] = "reranker"
    attributes["gen_ai.system"] = model.get("otel_gen_ai_system")
    attributes["gen_ai.request.model"] = model_params.get("llm")

    # Add recommended attributes by OpenTelemetry Gen AI
    attributes["gen_ai.usage.input_tokens"] = usage_details.input

    return attributes


def get_span_name(attributes: Mapping[str, AttributeValue]) -> str | None:
    span_name = attributes.get("magnet_ai.name")
    if not span_name:
        return None

    return str(span_name)


def get_span_type(attributes: Mapping[str, AttributeValue]) -> str | None:
    span_type = attributes.get("magnet_ai.type")
    if not span_type:
        return None

    return str(span_type)


def get_span_prompt_template(
    attributes: Mapping[str, AttributeValue],
) -> ObservedPromptTemplate | None:
    feature = ObservedFeature.from_otel_attributes(attributes)
    if not feature or feature.type.value != FeatureType.PROMPT_TEMPLATE:
        return None

    return ObservedPromptTemplate(
        name=feature.system_name.value,
        display_name=feature.display_name.value,
        variant=feature.variant.value,
    )


def get_span_model(
    attributes: Mapping[str, AttributeValue],
) -> ObservationModelDetails | None:
    name = attributes.get("magnet_ai.model.name")
    display_name = attributes.get("magnet_ai.model.display_name")
    provider = attributes.get("magnet_ai.model.provider")
    provider_display_name = attributes.get("magnet_ai.model.provider_display_name")
    otel_gen_ai_system = attributes.get("magnet_ai.model.otel_gen_ai_system")
    parameters_llm = attributes.get("magnet_ai.model.parameters.llm")
    parameters_temperature = attributes.get("magnet_ai.model.parameters.temperature")
    parameters_top_p = attributes.get("magnet_ai.model.parameters.top_p")
    parameters_max_tokens = attributes.get("magnet_ai.model.parameters.max_tokens")
    parameters_top_n = attributes.get("magnet_ai.model.parameters.top_n")
    parameters_tools = (
        json.loads(str(attributes.get("magnet_ai.model.tools")))
        if attributes.get("magnet_ai.model.tools")
        else None
    )
    if (
        not name
        and not display_name
        and not provider
        and not provider_display_name
        and not otel_gen_ai_system
        and not parameters_llm
        and parameters_temperature is None
        and parameters_top_p is None
        and parameters_max_tokens is None
        and parameters_top_n is None
        and parameters_tools is None
    ):
        return None

    return ObservationModelDetails(
        name=str(name),
        display_name=str(display_name),
        provider=str(provider),
        provider_display_name=str(provider_display_name),
        otel_gen_ai_system=str(otel_gen_ai_system),
        parameters={
            "llm": parameters_llm,
            "temperature": parameters_temperature,
            "top_p": parameters_top_p,
            "max_tokens": parameters_max_tokens,
            "top_n": parameters_top_n,
            "tools": parameters_tools,
        },
    )


def get_span_description(
    attributes: Mapping[str, AttributeValue],
) -> str | None:
    description = attributes.get("magnet_ai.description")
    if not description:
        return None

    return str(description)


def get_span_extra_data(
    attributes: Mapping[str, AttributeValue],
) -> dict[str, Any]:
    extra_data = {}
    for attribute_key, attribute_value in attributes.items():
        if attribute_key.startswith("magnet_ai.extra_data."):
            extra_data[attribute_key[len("magnet_ai.extra_data.") :]] = json.loads(
                str(attribute_value)
            )

    return extra_data


def get_span_input_output(
    attributes: Mapping[str, AttributeValue],
) -> tuple[Any, Any]:
    input = attributes.get("magnet_ai.input")
    output = attributes.get("magnet_ai.output")

    return (
        json.loads(str(input)) if input else None,
        json.loads(str(output)) if output else None,
    )


def get_span_usage_details(
    attributes: Mapping[str, AttributeValue],
) -> UsageDetails | None:
    input = attributes.get("magnet_ai.usage_details.input")
    input_details_units = attributes.get("magnet_ai.usage_details.input_details.units")
    input_details_standard = attributes.get(
        "magnet_ai.usage_details.input_details.standard"
    )
    input_details_cached = attributes.get(
        "magnet_ai.usage_details.input_details.cached"
    )
    output = attributes.get("magnet_ai.usage_details.output")
    output_details_units = attributes.get(
        "magnet_ai.usage_details.output_details.units"
    )
    output_details_standard = attributes.get(
        "magnet_ai.usage_details.output_details.standard"
    )
    output_details_reasoning = attributes.get(
        "magnet_ai.usage_details.output_details.reasoning"
    )
    total = attributes.get("magnet_ai.usage_details.total")
    if (
        input is None
        and input_details_units is None
        and input_details_standard is None
        and input_details_cached is None
        and output is None
        and output_details_units is None
        and output_details_standard is None
        and output_details_reasoning is None
        and total is None
    ):
        return None

    return UsageDetails(
        input=cast(int, input) if input is not None else None,
        input_details=UsageInputDetails(
            units=str(input_details_units),
            standard=cast(int, input_details_standard)
            if input_details_standard is not None
            else None,
            cached=cast(int, input_details_cached)
            if input_details_cached is not None
            else None,
        ),
        output=cast(int, output) if output is not None else None,
        output_details=UsageOutputDetails(
            units=str(output_details_units),
            standard=cast(int, output_details_standard)
            if output_details_standard is not None
            else None,
            reasoning=cast(int, output_details_reasoning)
            if output_details_reasoning is not None
            else None,
        ),
        total=cast(int, total) if total is not None else None,
    )


def get_span_cost_details(
    attributes: Mapping[str, AttributeValue],
) -> CostDetails | None:
    input = attributes.get("magnet_ai.cost_details.input")
    input_details_standard = attributes.get(
        "magnet_ai.cost_details.input_details.standard"
    )
    input_details_cached = attributes.get("magnet_ai.cost_details.input_details.cached")
    output = attributes.get("magnet_ai.cost_details.output")
    output_details_standard = attributes.get(
        "magnet_ai.cost_details.output_details.standard"
    )
    output_details_reasoning = attributes.get(
        "magnet_ai.cost_details.output_details.reasoning"
    )
    total = attributes.get("magnet_ai.cost_details.total")
    if (
        input is None
        and input_details_standard is None
        and input_details_cached is None
        and output is None
        and output_details_standard is None
        and output_details_reasoning is None
        and total is None
    ):
        return None

    return CostDetails(
        input=cast(float, input) if input is not None else None,
        input_details=CostInputDetails(
            standard=cast(float, input_details_standard)
            if input_details_standard is not None
            else None,
            cached=cast(float, input_details_cached)
            if input_details_cached is not None
            else None,
        ),
        output=cast(float, output) if output is not None else None,
        output_details=CostOutputDetails(
            standard=cast(float, output_details_standard)
            if output_details_standard is not None
            else None,
            reasoning=cast(float, output_details_reasoning)
            if output_details_reasoning is not None
            else None,
        ),
        total=cast(float, total) if total is not None else None,
    )
