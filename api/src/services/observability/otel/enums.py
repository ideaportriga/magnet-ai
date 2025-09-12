from enum import StrEnum


class OtelMetric(StrEnum):
    MAGNET_AI_FEATURE_DURATION = "magnet_ai.feature.call.duration"

    # Required metric by OpenTelemetry, measures duration of the LLM operation
    # See https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/#metric-gen_aiclientoperationduration
    GEN_AI_DURATION = "gen_ai.client.operation.duration"

    # Recommended metric by OpenTelemetry, measures usage (input and output tokens) of the LLM operation
    # See # See https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/#metric-gen_aiclienttokenusage
    GEN_AI_USAGE = "gen_ai.client.token.usage"

    # Unofficial Generative AI metric, used to measure cost (input and output) of the LLM operation
    GEN_AI_COST = "gen_ai.client.token.cost"


class OtelTokenType(StrEnum):
    INPUT = "input"
    OUTPUT = "output"
