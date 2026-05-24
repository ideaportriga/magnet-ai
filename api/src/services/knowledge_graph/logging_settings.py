from typing import Any

from services.observability.models import SpanExportMethod

from .models import KnowledgeGraphTracingLevel


def get_default_logging_settings() -> dict[str, Any]:
    return {
        "logging": {
            "sync_tracing_level": KnowledgeGraphTracingLevel.TOTALS_ONLY,
            "metadata_tracing_level": KnowledgeGraphTracingLevel.TOTALS_ONLY,
            "entity_extraction_tracing_level": KnowledgeGraphTracingLevel.TOTALS_ONLY,
        }
    }


def resolve_tracing_level(
    graph_settings: dict[str, Any] | None, key: str
) -> KnowledgeGraphTracingLevel:
    logging_cfg = (graph_settings or {}).get("logging") or {}
    raw = logging_cfg.get(key) or KnowledgeGraphTracingLevel.TOTALS_ONLY
    try:
        return KnowledgeGraphTracingLevel(raw)
    except ValueError:
        return KnowledgeGraphTracingLevel.TOTALS_ONLY


def tracing_level_to_export_method(
    level: KnowledgeGraphTracingLevel,
) -> SpanExportMethod | None:
    if level == KnowledgeGraphTracingLevel.OFF:
        return SpanExportMethod.IGNORE
    if level == KnowledgeGraphTracingLevel.FULL:
        return None
    return SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
