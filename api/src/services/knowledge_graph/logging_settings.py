from typing import Any

from .models import KnowledgeGraphTracingLevel


def get_default_logging_settings() -> dict[str, Any]:
    return {
        "logging": {
            "tracing_level": KnowledgeGraphTracingLevel.TOTALS_ONLY,
        }
    }
