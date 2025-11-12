from logging import getLogger

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from azure.monitor.opentelemetry.exporter import (
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)
from services.observability.models import MetricsExporterType, TracesExporterType
from services.observability.otel.exporters import SqlAlchemySpanExporter
from core.config.base import get_observability_settings, get_azure_settings

logger = getLogger(__name__)


def _get_metrics_exporters() -> list[MetricsExporterType]:
    observability_settings = get_observability_settings()

    if (
        not observability_settings.ENABLED
        or not observability_settings.METRICS_EXPORTERS
    ):
        return []

    result = []
    for exporter in observability_settings.METRICS_EXPORTERS.split(","):
        exporter = exporter.strip().lower()
        try:
            result.append(MetricsExporterType(exporter))
        except ValueError:
            logger.warning(f"Unknown metrics exporter type: {exporter}")
    return result


def get_metrics_readers() -> list[MetricReader]:
    readers: list[MetricReader] = []
    observability_settings = get_observability_settings()
    azure_settings = get_azure_settings()

    export_interval_millis = observability_settings.METRICS_EXPORT_INTERVAL_MS

    exporters = _get_metrics_exporters()
    for exporter in exporters:
        match exporter:
            case MetricsExporterType.OTLP_HTTP:
                readers.append(
                    PeriodicExportingMetricReader(
                        exporter=OTLPMetricExporter(),
                        export_interval_millis=export_interval_millis,
                    )
                )
            case MetricsExporterType.AZURE:
                connection_string = azure_settings.APPLICATIONINSIGHTS_CONNECTION_STRING
                if not connection_string:
                    logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING is not set")
                    continue

                try:
                    readers.append(
                        PeriodicExportingMetricReader(
                            exporter=AzureMonitorMetricExporter(
                                connection_string=connection_string
                            ),
                            export_interval_millis=export_interval_millis,
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to create Azure Monitor metrics reader: {e}")

    return readers


def _get_traces_exporters() -> list[TracesExporterType]:
    observability_settings = get_observability_settings()

    if (
        not observability_settings.ENABLED
        or not observability_settings.TRACES_EXPORTERS
    ):
        return []

    result = []
    for exporter in observability_settings.TRACES_EXPORTERS.split(","):
        exporter = exporter.strip().lower()
        try:
            result.append(TracesExporterType(exporter))
        except ValueError:
            logger.warning(f"Unknown traces exporter type: {exporter}")
    return result


def get_span_processors() -> list[SpanProcessor]:
    processors: list[SpanProcessor] = []
    observability_settings = get_observability_settings()

    max_export_batch_size = observability_settings.TRACES_MAX_EXPORT_BATCH_SIZE

    exporters = _get_traces_exporters()
    for exporter in exporters:
        match exporter:
            case TracesExporterType.INTERNAL:
                processors.append(
                    BatchSpanProcessor(
                        SqlAlchemySpanExporter(),
                        max_export_batch_size=max_export_batch_size,
                    )
                )
            case TracesExporterType.OTLP_HTTP:
                processors.append(
                    BatchSpanProcessor(
                        OTLPSpanExporter(), max_export_batch_size=max_export_batch_size
                    )
                )
            case TracesExporterType.AZURE:
                processors.append(
                    BatchSpanProcessor(
                        AzureMonitorTraceExporter(),
                        max_export_batch_size=max_export_batch_size,
                    )
                )

    return processors
