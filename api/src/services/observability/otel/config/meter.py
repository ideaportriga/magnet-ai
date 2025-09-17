from opentelemetry import metrics as otel_metrics
from opentelemetry.sdk.metrics import MeterProvider

from .resource import otel_resource
from .utils import get_metrics_readers

# Create meter provider
meter_provider = MeterProvider(
    resource=otel_resource,
    metric_readers=get_metrics_readers(),
)

# Set meter provider
otel_metrics.set_meter_provider(meter_provider)

# Create meter
otel_meter = otel_metrics.get_meter("magnet_ai", "1.0.0")
