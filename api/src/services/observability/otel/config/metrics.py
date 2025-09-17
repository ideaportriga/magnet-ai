# Create histogram to measure Magnet AI feature call duration
from services.observability.otel.enums import OtelMetric

from .meter import otel_meter

magnet_ai_feature_duration_histogram = otel_meter.create_histogram(
    name=OtelMetric.MAGNET_AI_FEATURE_DURATION,
    description="Magnet AI feature call duration",
    unit="s",
    explicit_bucket_boundaries_advisory=[
        0.01,
        0.02,
        0.04,
        0.08,
        0.16,
        0.32,
        0.64,
        1.28,
        2.56,
        5.12,
        10.24,
        20.48,
        40.96,
        81.92,
    ],
)

# Create OpenTelemetry Gen AI histogram to measure operation duration
gen_ai_duration_histogram = otel_meter.create_histogram(
    name=OtelMetric.GEN_AI_DURATION,
    description="GenAI operation duration",
    unit="s",
    explicit_bucket_boundaries_advisory=[
        0.01,
        0.02,
        0.04,
        0.08,
        0.16,
        0.32,
        0.64,
        1.28,
        2.56,
        5.12,
        10.24,
        20.48,
        40.96,
        81.92,
    ],
)


# Create OpenTelemetry Gen AI histogram to measure number of input and output tokens used
gen_ai_usage_histogram = otel_meter.create_histogram(
    name=OtelMetric.GEN_AI_USAGE,
    description="Measures number of input and output tokens used",
    unit="token",
    explicit_bucket_boundaries_advisory=[
        1,
        4,
        16,
        64,
        256,
        1024,
        4096,
        16384,
        65536,
        262144,
        1048576,
        4194304,
        16777216,
        67108864,
    ],
)

# Create unofficial OpenTelemetry Gen AI histogram to measure cost of input and output tokens
gen_ai_cost_histogram = otel_meter.create_histogram(
    name=OtelMetric.GEN_AI_COST,
    description="Measures cost of input and output tokens",
    unit="USD",
    explicit_bucket_boundaries_advisory=[
        0.00005,
        0.0001,
        0.001,
        0.01,
        0.02,
        0.05,
        0.1,
        0.2,
        0.5,
        1.0,
        2.0,
        5.0,
        10.0,
    ],
)
