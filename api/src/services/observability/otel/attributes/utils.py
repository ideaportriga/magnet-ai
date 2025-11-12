import json
from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel


def clean_attributes(
    attributes: Mapping[str, AttributeValue | None],
) -> Mapping[str, AttributeValue]:
    return {k: v for k, v in attributes.items() if v is not None}


def expand_fields(
    prefix: str, fields: Any, exclude: list[str] = [], json_dump: bool = False
):
    if not fields:
        return {}

    attributes: Mapping[str, AttributeValue | None] = {}

    if isinstance(fields, BaseModel):
        fields = fields.model_dump()
    elif not hasattr(fields, "items"):
        fields = asdict(fields)

    for field_name, field_value in fields.items():
        if field_name not in exclude:
            if json_dump:
                attributes[f"{prefix}.{field_name}"] = json.dumps(field_value)
            else:
                attributes[f"{prefix}.{field_name}"] = field_value

    return attributes
