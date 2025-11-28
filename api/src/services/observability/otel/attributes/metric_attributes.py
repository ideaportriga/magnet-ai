from collections.abc import Mapping
from logging import getLogger

from opentelemetry.util.types import AttributeValue

from services.observability.models import (
    LLMType,
    ObservationModelDetails,
    ObservedFeature,
    ObservedGlobals,
)
from services.observability.otel.enums import OtelMetric, OtelTokenType

from .utils import clean_attributes

logger = getLogger(__name__)


def create_otel_metric_attributes(
    metric: OtelMetric,
    llm_or_feature: LLMType | ObservedFeature,
    *,
    global_fields: ObservedGlobals | None = None,
    model_details: ObservationModelDetails | None = None,
    token_type: OtelTokenType | None = None,
):
    attributes: Mapping[str, AttributeValue | None] = {}

    if global_fields:
        attributes.update(global_fields.to_otel_attributes())

    if isinstance(llm_or_feature, LLMType):
        model = model_details or {}
        model_params = model.get("parameters") or {}
        if metric == OtelMetric.GEN_AI_DURATION:
            attributes["gen_ai.operation.name"] = llm_or_feature.otel_operation_name
            attributes["gen_ai.system"] = model.get("otel_gen_ai_system")
            attributes["gen_ai.request.model"] = model_params.get("llm")
            attributes["gen_ai.response.model"] = model_params.get("llm")
        elif metric in [OtelMetric.GEN_AI_USAGE, OtelMetric.GEN_AI_COST]:
            attributes["gen_ai.operation.name"] = llm_or_feature.otel_operation_name
            attributes["gen_ai.system"] = model.get("otel_gen_ai_system")
            attributes["gen_ai.token.type"] = token_type
            attributes["gen_ai.request.model"] = model_params.get("llm")
            attributes["gen_ai.response.model"] = model_params.get("llm")
        else:
            logger.warning(f"Unknown metric: {metric} for {llm_or_feature}")
    else:
        if metric == OtelMetric.MAGNET_AI_FEATURE_DURATION:
            attributes.update(llm_or_feature.to_otel_attributes())
        else:
            logger.warning(f"Unknown metric: {metric} for {llm_or_feature}")

    return clean_attributes(attributes)
