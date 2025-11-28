from __future__ import annotations

from typing import Any, Dict, List, Optional

from type_defs.pagination import FilterObject


def metadata_filter_to_filter_object(
    metadata_filter: Optional[List[Dict[str, Any]]],
) -> FilterObject:
    if not metadata_filter:
        return FilterObject({})

    and_clauses: List[Dict[str, Any]] = []

    for filter_item in metadata_filter:
        field_name = filter_item.get("field")
        conditions = filter_item.get("conditions") or []
        if not field_name or not isinstance(conditions, list):
            continue

        or_clauses: List[Dict[str, Any]] = []

        for condition in conditions:
            condition_type = condition.get("type")
            operator = condition.get("operator")

            if condition_type == "value":
                # Map to $eq / $ne with fallback to empty string if value is falsy
                op = "$eq" if operator == "equal" else "$ne"
                value = condition.get("value") or ""
                transformed = {field_name: {op: value}}

            elif condition_type == "empty":
                # Empty is represented by membership in [None, ""]
                op = "$in" if operator == "equal" else "$nin"
                transformed = {field_name: {op: [None, ""]}}

            elif condition_type == "exists":
                # Existence check maps to $exists bool
                transformed = {
                    field_name: {"$exists": True if operator == "equal" else False}
                }

            else:
                # Unsupported or unknown condition type
                continue

            or_clauses.append(transformed)

        if not or_clauses:
            continue

        if len(or_clauses) == 1:
            and_clauses.append(or_clauses[0])
        else:
            and_clauses.append({"$or": or_clauses})

    # If nothing valid was produced, return an empty object
    if not and_clauses:
        return FilterObject({})

    return FilterObject({"$and": and_clauses})
