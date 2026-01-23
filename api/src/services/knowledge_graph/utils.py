from __future__ import annotations

from typing import Any

from .models import MetadataMultiValueContainer


def normalize_metadata_value(value: Any) -> Any:
    """Normalize metadata values for JSON storage.

    Converts MetadataMultiValueContainer (and other non-JSON containers) into
    JSON-friendly structures while preserving nested values.
    """
    if isinstance(value, MetadataMultiValueContainer):
        return [normalize_metadata_value(v) for v in value.values]
    if isinstance(value, dict):
        return {k: normalize_metadata_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalize_metadata_value(v) for v in value]
    return value
