import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Dict, Generic, Sequence, TypedDict, TypeVar, override

from bson import ObjectId
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel


class MetricsExporterType(StrEnum):
    OTLP_HTTP = "otlp-http"
    AZURE = "azure"


class TracesExporterType(StrEnum):
    INTERNAL = "internal"
    OTLP_HTTP = "otlp-http"
    AZURE = "azure"


class ObservabilityLevel(StrEnum):
    """
    Defines the level of observability logging for features like Prompt Templates.
    
    - NONE: No logging at all - the span and metrics are completely skipped
    - METADATA_ONLY: Logs metadata (tokens, cost, latency, model info) but excludes input/output content
    - FULL: Full logging including input and output content (default behavior)
    """
    NONE = "none"
    METADATA_ONLY = "metadata-only"
    FULL = "full"


class SpanType(StrEnum):
    SPAN = "span"
    CHAT_COMPLETION = "chat"
    EMBEDDING = "embed"
    RERANKING = "rerank"
    SEARCH = "search"
    TOOL = "tool"


class FeatureType(Enum):
    # MagnetAI Features
    PROMPT_TEMPLATE = {
        "value": "prompt-template",
        "otel_name": "prompt_template",
        "span_type": SpanType.CHAT_COMPLETION,
    }
    KNOWLEDGE_SOURCE = {
        "value": "knowledge-source",
        "otel_name": "knowledge_source",
        "span_type": SpanType.SPAN,
    }
    RETRIEVAL_TOOL = {
        "value": "retrieval-tool",
        "otel_name": "retrieval_tool",
        "span_type": SpanType.SPAN,
    }
    RAG_TOOL = {
        "value": "rag-tool",
        "otel_name": "rag_tool",
        "span_type": SpanType.SPAN,
    }
    AGENT = {
        "value": "agent",
        "otel_name": "agent",
        "span_type": SpanType.SPAN,
    }
    KNOWLEDGE_GRAPH = {
        "value": "knowledge-graph",
        "otel_name": "knowledge_graph",
        "span_type": SpanType.SPAN,
    }
    # Standard LLM APIs
    CHAT_COMPLETION = {
        "value": "chat-completion-api",
        "otel_name": "chat_completion",
        "span_type": SpanType.CHAT_COMPLETION,
    }
    EMBEDDING = {
        "value": "embedding-api",
        "otel_name": "embedding",
        "span_type": SpanType.EMBEDDING,
    }
    RERANKING = {
        "value": "reranking-api",
        "otel_name": "reranker",
        "span_type": SpanType.RERANKING,
    }

    def __init__(self, data):
        self._data = data

    @property
    def value(self) -> str:
        return self._data["value"]

    @property
    def otel_name(self) -> str:
        return self._data["otel_name"]

    @property
    def span_type(self) -> SpanType:
        return self._data["span_type"]

    @staticmethod
    def from_otel_name(otel_name: str) -> "FeatureType | None":
        for feature_type in FeatureType:
            if feature_type.otel_name == otel_name:
                return feature_type
        return None


class LLMType(Enum):
    CHAT_COMPLETION = {
        "span_type": "chat",
        "otel_operation_name": "chat",
    }
    EMBEDDING = {
        "span_type": "embed",
        "otel_operation_name": "embeddings",
    }
    RERANKING = {
        "span_type": "rerank",
        "otel_operation_name": "reranker",
    }

    def __init__(self, data):
        self._data = data

    @property
    def span_type(self) -> str:
        """
        Returns the span type used in traces.
        """
        return self._data["span_type"]

    @property
    def otel_operation_name(self) -> str:
        """
        Returns the OpenTelemetry attribute with operation name. This values follows OpenTelemetry GenAI semantic convention.
        """
        return self._data["otel_operation_name"]


class SpanExportMethod(StrEnum):
    IGNORE = "ignore"
    IGNORE_BUT_USE_FOR_TOTALS = "ignore-but-use-for-totals"


# This interface describes params that can be passed to the decorator
# Specify only those fields that can be passed to the observability decorator from the rest of the code
class DecoratorParams(TypedDict, total=False):
    enabled: bool
    name: str | None
    type: SpanType | None
    description: str | None
    extra_data: Dict[str, Any] | None
    capture_input: bool
    capture_output: bool
    trace_enabled: bool
    trace_name: str | None
    channel: str | None
    source: str | None
    consumer_type: str | None
    consumer_name: str | None
    user_id: str | None


# This interface describes params that can be passed to the trace update method
# Specify only those fields that can be passed to the trace update method from the rest of the code
class TraceParams(TypedDict, total=False):
    name: str | None
    type: str | None
    extra_data: Dict[str, Any] | None
    user_id: str | None


class ObservedPromptTemplate(TypedDict, total=False):
    name: str | None
    display_name: str | None
    variant: str | None


class ObservationModelDetails(TypedDict, total=False):
    name: str | None
    display_name: str | None
    provider: str | None
    provider_display_name: str | None
    otel_gen_ai_system: str | None
    parameters: dict[str, Any] | None


class UsageInputDetails(BaseModel):
    units: str | None = "tokens"
    standard: int | None = None
    cached: int | None = None


class UsageOutputDetails(BaseModel):
    units: str | None = "tokens"
    standard: int | None = None
    reasoning: int | None = None


class UsageDetails(BaseModel):
    input: int | None = None
    input_details: UsageInputDetails | None = None
    output: int | None = None
    output_details: UsageOutputDetails | None = None
    total: int | None = None


class CostInputDetails(BaseModel):
    standard: float | None = None
    cached: float | None = None


class CostOutputDetails(BaseModel):
    standard: float | None = None
    reasoning: float | None = None


class CostDetails(BaseModel):
    input: float | None = None
    input_details: CostInputDetails | None = None
    output: float | None = None
    output_details: CostOutputDetails | None = None
    total: float | None = None


class TraceCostDetails(BaseModel):
    embed: float | None = None
    chat: float | None = None
    rerank: float | None = None
    total: float | None = None


T = TypeVar("T")


@dataclass
class ObservabilityField(Generic[T]):
    otel_name: str
    value: T


class ObservabilityFields(ABC):
    @abstractmethod
    def get_prefix(self) -> str:
        pass

    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        attr_name_prefix = prefix or self.get_prefix()
        return {
            f"{attr_name_prefix}.{attr.otel_name}": attr.value
            for _, attr in vars(self).items()
            if isinstance(attr, ObservabilityField)
            and isinstance(attr.value, (str, bool, int, float, Sequence))
        }

    def load_otel_attributes(
        self,
        attributes: Mapping[str, AttributeValue],
        *,
        prefix: str | None = None,
        exclude: set[str] | None = None,
    ):
        attr_name_prefix = prefix or self.get_prefix()
        for attr_name, attr_value in attributes.items():
            field_name = attr_name.removeprefix(f"{attr_name_prefix}.")
            if hasattr(self, field_name) and field_name not in (exclude or {}):
                field = getattr(self, field_name)
                if isinstance(field, ObservabilityField):
                    field.value = attr_value

    def load_otel_baggage(
        self, baggage: Mapping[str, object], *, prefix: str | None = None
    ):
        name_prefix = prefix or ""
        for name, value in baggage.items():
            if name_prefix:
                name = name.removeprefix(f"{name_prefix}.")
            if hasattr(self, name):
                field = getattr(self, name)
                if isinstance(field, ObservabilityField):
                    field.value = value


class ObservabilityConfig(ObservabilityFields):
    __prefix = "magnet_ai.config"

    def __init__(self, span_export_method: SpanExportMethod | None = None):
        self.span_export_method = ObservabilityField[SpanExportMethod | None](
            "span_export_method", span_export_method
        )

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        instance = cls()
        instance.load_otel_attributes(attributes, prefix=prefix)
        return instance

    @classmethod
    def from_otel_baggage(cls, baggage: Mapping[str, object]):
        instance = cls()
        instance.load_otel_baggage(baggage, prefix="config")
        return instance


class ObservedGlobals(ObservabilityFields):
    __prefix = "magnet_ai"

    def __init__(
        self,
        channel: str | None = None,
        source: str | None = None,
        user_id: str | None = None,
        consumer_name: str | None = None,
        consumer_type: str | None = None,
        x_attributes: Dict[str, Any] | None = None,
    ):
        self.channel = ObservabilityField[str | None]("channel", channel)
        self.source = ObservabilityField[str | None]("source", source)
        self.user_id = ObservabilityField[str | None]("user_id", user_id)
        self.consumer_name = ObservabilityField[str | None](
            "consumer_name", consumer_name
        )
        self.consumer_type = ObservabilityField[str | None](
            "consumer_type", consumer_type
        )
        self.x_attributes = ObservabilityField[Dict[str, Any] | None](
            "x_attributes", x_attributes
        )

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @override
    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        x_attributes: Mapping[str, AttributeValue] = {}
        if self.x_attributes.value:
            x_attributes_otel_attr_prefix = (
                f"{prefix or self.get_prefix()}.{self.x_attributes.otel_name}"
            )
            for name, value in self.x_attributes.value.items():
                x_attributes[f"{x_attributes_otel_attr_prefix}.{name}"] = json.dumps(
                    value
                )

        return {**super().to_otel_attributes(prefix=prefix), **x_attributes}

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        instance = cls()
        instance.load_otel_attributes(
            attributes, prefix=prefix, exclude={instance.x_attributes.otel_name}
        )

        x_attributes = {}
        x_attributes_otel_attr_prefix = (
            f"{prefix or instance.get_prefix()}.{instance.x_attributes.otel_name}"
        )
        for name, value in attributes.items():
            if name.startswith(f"{x_attributes_otel_attr_prefix}."):
                x_attributes[name[len(f"{x_attributes_otel_attr_prefix}.") :]] = (
                    json.loads(str(value))
                )
        instance.x_attributes.value = x_attributes

        return instance

    @classmethod
    def from_otel_baggage(cls, baggage: Mapping[str, object]):
        instance = cls()
        instance.load_otel_baggage(baggage)
        return instance


class TraceObservabilityFields(ObservabilityFields):
    __prefix = "magnet_ai.trace"

    def __init__(
        self,
        name: str | None = None,
        type: str | None = None,
        extra_data: Dict[str, Any] | None = None,
    ):
        self.name = ObservabilityField[str | None]("name", name)
        self.type = ObservabilityField[str | None]("type", type)
        self.extra_data = ObservabilityField[Dict[str, Any] | None](
            "extra_data", extra_data
        )

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @override
    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        extra_data_attributes: Mapping[str, AttributeValue] = {}

        if self.extra_data.value:
            extra_data_otel_attr_prefix = (
                f"{prefix or self.get_prefix()}.{self.extra_data.otel_name}"
            )
            for name, value in self.extra_data.value.items():
                extra_data_attributes[f"{extra_data_otel_attr_prefix}.{name}"] = (
                    json.dumps(value, default=str)
                )

        return {**super().to_otel_attributes(prefix=prefix), **extra_data_attributes}

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        instance = cls()
        instance.load_otel_attributes(
            attributes, prefix=prefix, exclude={instance.extra_data.otel_name}
        )

        extra_data = {}
        extra_data_otel_attr_prefix = (
            f"{prefix or instance.get_prefix()}.{instance.extra_data.otel_name}"
        )
        for attribute_key, attribute_value in attributes.items():
            if attribute_key.startswith(f"{extra_data_otel_attr_prefix}."):
                extra_data[attribute_key[len(f"{extra_data_otel_attr_prefix}.") :]] = (
                    json.loads(str(attribute_value))
                )
        instance.extra_data.value = extra_data

        return instance


class ObservedFeature(ObservabilityFields):
    __prefix = "magnet_ai.feature"
    __type_otel_attr_name = "type"

    def __init__(
        self,
        type: FeatureType,
        id: str | None = None,
        system_name: str | None = None,
        display_name: str | None = None,
        variant: str | None = None,
        observability_level: ObservabilityLevel | None = None,
    ):
        self.type = ObservabilityField[FeatureType](self.__type_otel_attr_name, type)
        self.id = ObservabilityField[str | None]("id", id)
        self.system_name = ObservabilityField[str | None]("system_name", system_name)
        self.display_name = ObservabilityField[str | None]("display_name", display_name)
        self.variant = ObservabilityField[str | None]("variant", variant)
        # Observability level determines what gets logged:
        # - NONE: skip all logging
        # - METADATA_ONLY: log metadata (tokens, cost, latency) but not input/output
        # - FULL: log everything including input/output (default)
        self.observability_level = observability_level or ObservabilityLevel.FULL

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @override
    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        type_otel_attr_name = f"{prefix or self.get_prefix()}.{self.type.otel_name}"
        type_otel_attr_value = self.type.value.otel_name
        return {
            type_otel_attr_name: type_otel_attr_value,
            **super().to_otel_attributes(prefix=prefix),
        }

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        type_otel_attr_name = f"{prefix or cls.__prefix}.{cls.__type_otel_attr_name}"
        type_otel_attr_value = attributes.get(type_otel_attr_name)
        feature_type = FeatureType.from_otel_name(str(type_otel_attr_value))
        if not feature_type:
            return None

        instance = cls(feature_type)
        instance.load_otel_attributes(
            attributes, prefix=prefix, exclude={cls.__type_otel_attr_name}
        )

        return instance


class ObservedFeatureInstance(ObservabilityFields):
    __prefix = "magnet_ai.feature"
    __instance_id_otel_attr_name = "instance_id"

    def __init__(
        self,
        feature: ObservedFeature,
        id: str | None = None,
        span_id: str | None = None,
    ):
        self.id = ObservabilityField[str](
            self.__instance_id_otel_attr_name, id or str(ObjectId())
        )
        self.span_id = span_id
        self.feature = feature

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @override
    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        return {
            **super().to_otel_attributes(prefix=prefix),
            **self.feature.to_otel_attributes(prefix=prefix),
        }

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        feature = ObservedFeature.from_otel_attributes(attributes, prefix=prefix)
        if not feature:
            return None

        instance_id_attr_name = (
            f"{prefix or cls.__prefix}.{cls.__instance_id_otel_attr_name}"
        )
        instance_id = attributes.get(instance_id_attr_name)
        instance = cls(feature, str(instance_id) if instance_id else None)
        instance.load_otel_attributes(attributes, prefix=prefix, exclude={"id"})
        return instance


class ObservedConversation(ObservabilityFields):
    __prefix = "magnet_ai.conversation"

    def __init__(self, id: str | None = None, data: Dict[str, Any] | None = None):
        self.id = ObservabilityField[str | None]("id", id)
        self.data = ObservabilityField[Dict[str, Any] | None]("data", data)

    @override
    def get_prefix(self) -> str:
        return self.__prefix

    @override
    def to_otel_attributes(
        self, *, prefix: str | None = None
    ) -> Mapping[str, AttributeValue]:
        data: Mapping[str, AttributeValue] = {}
        if self.data.value:
            data_otel_attr_prefix = (
                f"{prefix or self.get_prefix()}.{self.data.otel_name}"
            )
            for name, value in self.data.value.items():
                data[f"{data_otel_attr_prefix}.{name}"] = json.dumps(value)

        return {**super().to_otel_attributes(prefix=prefix), **data}

    @classmethod
    def from_otel_attributes(
        cls, attributes: Mapping[str, AttributeValue], *, prefix: str | None = None
    ):
        instance = cls()
        instance.load_otel_attributes(
            attributes, prefix=prefix, exclude={instance.data.otel_name}
        )

        data = {}
        data_otel_attr_prefix = (
            f"{prefix or instance.get_prefix()}.{instance.data.otel_name}"
        )
        for name, value in attributes.items():
            if name.startswith(f"{data_otel_attr_prefix}."):
                data[name[len(f"{data_otel_attr_prefix}.") :]] = json.loads(str(value))
        instance.data.value = data

        return instance

    @classmethod
    def from_otel_baggage(cls, baggage: Mapping[str, object]):
        instance = cls()
        instance.load_otel_baggage(baggage, prefix="conversation")
        return instance


# region Span related classes


# This interface describes params that can be passed to the span update method
# Specify only those fields that can be passed to the span update method from the rest of the code
class SpanParams(TypedDict, total=False):
    name: str | None
    start_time: datetime | None
    end_time: datetime | None
    status: str | None
    status_message: str | None
    prompt_template: ObservedPromptTemplate | None
    model: ObservationModelDetails | None
    description: str | None
    extra_data: Dict[str, Any] | None
    input: Any | None
    output: Any | None
    usage_details: UsageDetails | None
    cost_details: CostDetails | None
    conversation_id: str | None


# This class is used to collect and transfer span data internally inside observability module
# It's not a 1:1 match with SpanParams, because it can include fields that are callculated internally
@dataclass
class SpanFields:
    name: str | None = None
    type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None
    status_message: str | None = None
    prompt_template: ObservedPromptTemplate | None = None
    model: ObservationModelDetails | None = None
    description: str | None = None
    extra_data: Dict[str, Any] | None = None
    input: Any | None = None
    output: Any | None = None
    usage_details: UsageDetails | None = None
    cost_details: CostDetails | None = None
    conversation_id: str | None = None


# endregion


class BaggageParams(TypedDict, total=False):
    channel: str | None
    source: str | None
    user_id: str | None
    consumer_name: str | None
    consumer_type: str | None
    conversation_id: str | None
    conversation_data: Dict[str, Any] | None


# region Metrics summary related classes


class MetricsSummaryBreakdown(BaseModel):
    name: str | bool | None = None
    count: int


class ResolutionSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class TopicSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class AnswerFeedbackSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class AnswerSummary(BaseModel):
    feedback: AnswerFeedbackSummary
    copy_rate: float


class ChannelSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class LanguageSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class SentimentSummary(BaseModel):
    breakdown: list[MetricsSummaryBreakdown]


class RagMetricsSummary(BaseModel):
    total_calls: int
    unique_user_count: int
    avg_latency: float
    avg_cost: float
    total_cost: float
    resolution_summary: ResolutionSummary
    topic_summary: TopicSummary
    answer_summary: AnswerSummary
    language_summary: LanguageSummary


class AgentMetricSummary(BaseModel):
    total_conversations: int
    unique_user_count: int
    avg_duration: float
    avg_cost: float
    copy_rate: float
    avg_messages_count: float
    total_cost: float
    avg_tool_call_latency: float
    resolution_summary: ResolutionSummary
    channel_summary: ChannelSummary
    sentiment_summary: SentimentSummary
    feedback_summary: AnswerFeedbackSummary
    topics_summary: TopicSummary
    feedback_rate: float
    language_summary: LanguageSummary


class LlmMetricsSummary(BaseModel):
    total_calls: int
    unique_user_count: int
    avg_latency: float
    avg_cost: float
    total_cost: float
    error_rate: float


class MetricsTopList(TypedDict):
    name: str
    count: int
    avg_latency: float
    avg_total_cost: float
    unique_user_count: int


class MetricsItem(TypedDict):
    _id: str
    name: str
    feature_id: str
    feature_system_name: str
    variant: str
    start_time: datetime
    end_time: datetime
    channel: str
    source: str
    latency: float
    extra_data: dict[str, Any]
    trace_id: str | None
    cost: float
    consumer_name: str
    consumer_type: str


class MetricsQueryResult(TypedDict):
    items: list[MetricsItem]
    total: int
    limit: int
    offset: int


class OptionsRagResponse(BaseModel):
    organizations: list[str]
    topics: list[str]
    languages: list[str]
    consumer_names: list[str]


class OptionsLlmResponse(BaseModel):
    organizations: list[str]
    consumer_names: list[str]


class OptionsAgentResponse(BaseModel):
    organizations: list[str]
    topics: list[str]
    tools: list[str]
    consumer_names: list[str]
    languages: list[str]


class ConversationMetricsSummary(BaseModel):
    total_conversations: int
    unique_user_count: int
    avg_conversation_cost: float
    avg_response_time: float
    feedback_likes: int
    feedback_dislikes: int


# endregion
