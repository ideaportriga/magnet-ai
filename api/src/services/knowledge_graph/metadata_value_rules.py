"""Enforce extraction field settings on LLM metadata output.

The LLM is asked to respect each field's "Multiple Values" flag and allowed
values, but it does not always do so. These helpers validate and autocorrect
the parsed output and merge per-segment results into one value set per
document.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldRule:
    is_multiple: bool = False
    # Normalized key -> canonical allowed value. Empty = no restriction.
    allowed: dict[str, str] = field(default_factory=dict)


def _normalize_key(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _identity_key(value: Any) -> str:
    """Hashable key used to de-duplicate and count values."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    return f"{type(value).__name__}:{value}"


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return not stripped or stripped.casefold() == "null"
    if isinstance(value, dict):
        return len(value) == 0
    return False


def _flatten(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        out: list[Any] = []
        for v in value:
            out.extend(_flatten(v))
        return out
    return [] if _is_empty(value) else [value]


def _unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for v in values:
        key = _identity_key(v)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def build_field_rules(
    extraction_field_settings: dict[str, dict[str, Any]],
) -> dict[str, FieldRule]:
    rules: dict[str, FieldRule] = {}
    for raw_name, settings in (extraction_field_settings or {}).items():
        name = str(raw_name or "").strip()
        if not name:
            continue
        settings = settings if isinstance(settings, dict) else {}
        value_type = str(settings.get("value_type") or "").strip().lower()

        allowed: dict[str, str] = {}
        allowed_raw = settings.get("allowed_values")
        if isinstance(allowed_raw, list):
            for av in allowed_raw:
                if not isinstance(av, dict):
                    continue
                val = str(av.get("value") or "").strip()
                if val:
                    allowed.setdefault(_normalize_key(val), val)

        rules[name] = FieldRule(
            is_multiple=bool(settings.get("is_multiple")) or value_type == "array",
            allowed=allowed,
        )
    return rules


def validate_extracted(
    extracted: dict[str, Any], rules: dict[str, FieldRule]
) -> tuple[dict[str, Any], list[str]]:
    """Clean one LLM response against the field rules.

    Returns the cleaned mapping (scalar for single-value fields, list for
    multi-value fields; empty fields omitted) and human-readable violations
    that could not be autocorrected.
    """
    cleaned: dict[str, Any] = {}
    violations: list[str] = []

    for raw_key, raw_value in (extracted or {}).items():
        name = str(raw_key or "").strip()
        rule = rules.get(name)
        if rule is None:
            continue

        values = _flatten(raw_value)
        if rule.allowed:
            matched: list[Any] = []
            for v in values:
                canonical = rule.allowed.get(_normalize_key(v))
                if canonical is None:
                    violations.append(
                        f'field "{name}": {json.dumps(v, default=str, ensure_ascii=False)} '
                        "is not an allowed value (allowed: "
                        f"{', '.join(rule.allowed.values())})"
                    )
                else:
                    matched.append(canonical)
            values = matched

        values = _unique(values)
        if not values:
            continue

        if rule.is_multiple:
            cleaned[name] = values
            continue

        if len(values) > 1:
            violations.append(
                f'field "{name}" allows only one value, but got '
                f"{len(values)}: "
                f"{', '.join(json.dumps(v, default=str, ensure_ascii=False) for v in values)}"
            )
        cleaned[name] = values[0]

    return cleaned, violations


class DocumentMetadataAccumulator:
    """Merge cleaned per-segment/per-chunk results into one document result.

    Single-value fields keep the most frequent value (ties go to the value
    seen first); multi-value fields keep all unique values in first-seen order.
    """

    def __init__(self, rules: dict[str, FieldRule]) -> None:
        self._rules = rules
        self._values: dict[str, dict[str, Any]] = {}
        self._counts: dict[str, Counter[str]] = {}

    def add(self, cleaned: dict[str, Any]) -> None:
        for name, value in (cleaned or {}).items():
            values = self._values.setdefault(name, {})
            counts = self._counts.setdefault(name, Counter())
            for v in _flatten(value):
                key = _identity_key(v)
                values.setdefault(key, v)
                counts[key] += 1

    def finalize(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, values in self._values.items():
            if not values:
                continue
            rule = self._rules.get(name, FieldRule())
            if rule.is_multiple:
                out[name] = list(values.values())
                continue
            counts = self._counts[name]
            # dict preserves insertion order, so max() returns the first-seen
            # value among those with the highest count.
            best_key = max(values, key=lambda k: counts[k])
            out[name] = values[best_key]
        return out
