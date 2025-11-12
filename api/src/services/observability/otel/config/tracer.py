from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider

from .resource import otel_resource
from .utils import get_span_processors

# Create tracer provider
otel_tracer_provider = TracerProvider(resource=otel_resource)

# Add span processors
for processor in get_span_processors():
    otel_tracer_provider.add_span_processor(processor)

# Set tracer provider
otel_trace.set_tracer_provider(otel_tracer_provider)

# Create tracer
otel_tracer = otel_trace.get_tracer("magnet_ai", "1.0.0")
