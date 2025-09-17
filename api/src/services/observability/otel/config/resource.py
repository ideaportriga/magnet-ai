import uuid

from opentelemetry.sdk.resources import Resource

otel_resource = Resource(
    attributes={
        "service.name": "magnet-ai",
        "service.instance.id": str(uuid.uuid4()),
        "telemetry.sdk.language": "python",
        "telemetry.sdk.version": "1.35.0",
    }
)
