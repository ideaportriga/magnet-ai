import os
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

logger = getLogger(__name__)

observability_enabled = os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "true"


def _get_metrics_exporters() -> list[MetricsExporterType]:
    metrics_exporters = os.getenv("OBSERVABILITY_METRICS_EXPORTERS")
    if not observability_enabled or not metrics_exporters:
        return []

    result = []
    for exporter in metrics_exporters.split(","):
        exporter = exporter.strip().lower()
        try:
            result.append(MetricsExporterType(exporter))
        except ValueError:
            logger.warning(f"Unknown metrics exporter type: {exporter}")
    return result


def get_metrics_readers() -> list[MetricReader]:
    readers: list[MetricReader] = []

    export_interval_millis = int(
        os.getenv("OBSERVABILITY_METRICS_EXPORT_INTERVAL_MS", "3000")
    )

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
                connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
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
    traces_exporters = os.getenv("OBSERVABILITY_TRACES_EXPORTERS")
    if not observability_enabled or not traces_exporters:
        return []

    result = []
    for exporter in traces_exporters.split(","):
        exporter = exporter.strip().lower()
        try:
            result.append(TracesExporterType(exporter))
        except ValueError:
            logger.warning(f"Unknown traces exporter type: {exporter}")
    return result


def get_span_processors() -> list[SpanProcessor]:
    processors: list[SpanProcessor] = []

    max_export_batch_size = int(
        os.getenv("OBSERVABILITY_TRACES_MAX_EXPORT_BATCH_SIZE", "100")
    )

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
