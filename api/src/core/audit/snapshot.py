"""Snapshot + diff helpers for the audit listener.

A snapshot is a JSON-serializable dict capturing the persisted state of a
SQLAlchemy model. It is used in three places:

  - ``snapshot_before`` (state right before the change)
  - ``snapshot_after``  (state right after the change)
  - input to ``compute_diff`` (a flat per-path delta for the audit row)

Secret-bearing columns (declared via ``Auditable.__audit_secret_fields__``)
are masked: the key is kept so "this field changed" remains visible, but
the value is replaced with empty strings.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping
from uuid import UUID

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import History

from .mixin import Auditable


def serialize_value(value: Any) -> Any:
    """Convert a Python value into something JSON-roundtrippable.

    SQLAlchemy hands us UUIDs, datetimes, Decimals, etc. — JSONB can store
    them once serialized. ``dict`` / ``list`` are traversed recursively.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Mapping):
        return {str(k): serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [serialize_value(v) for v in value]
    # Last-resort fallback — give the listener something to write instead
    # of crashing the whole flush.
    return str(value)


def _mask_secrets(
    snapshot: dict[str, Any], secret_fields: Iterable[str]
) -> dict[str, Any]:
    for field in secret_fields:
        if field not in snapshot:
            continue
        value = snapshot[field]
        if isinstance(value, dict):
            snapshot[field] = {k: "" for k in value.keys()}
        elif value is None:
            snapshot[field] = None
        else:
            snapshot[field] = ""
    return snapshot


def snapshot_current(obj: Auditable) -> dict[str, Any]:
    """Capture the model's current persisted column values.

    Only mapped columns are included — relationships / hybrids are skipped.
    Reads from in-memory attributes, so the result reflects what is about
    to be flushed (not what's currently in the DB).
    """
    mapper = inspect(obj.__class__)
    result: dict[str, Any] = {}
    for column in mapper.columns:
        key = column.key
        try:
            value = getattr(obj, key)
        except Exception:
            continue
        result[key] = serialize_value(value)
    return _mask_secrets(result, obj.__audit_secret_fields__)


def snapshot_before_update(obj: Auditable) -> dict[str, Any]:
    """Build a snapshot of the row's state BEFORE the pending update.

    For each mapped column, prefers the SQLAlchemy attribute history's
    ``deleted`` slot (the previous DB-loaded value before re-assignment)
    and falls back to ``unchanged`` (untouched columns keep their value).
    Called from ``before_flush`` while the session still has the prior
    state attached to the instance.
    """
    state = inspect(obj)
    mapper = inspect(obj.__class__)
    result: dict[str, Any] = {}
    for column in mapper.columns:
        key = column.key
        attr = state.attrs.get(key)
        if attr is None:
            continue
        history: History = attr.history
        if history.deleted:
            value = history.deleted[0]
        elif history.unchanged:
            value = history.unchanged[0]
        else:
            # New-but-not-yet-flushed attributes have no history; fall
            # back to the current in-memory value (which is the new one).
            try:
                value = getattr(obj, key)
            except Exception:
                continue
        result[key] = serialize_value(value)
    return _mask_secrets(result, obj.__audit_secret_fields__)


def compute_diff(
    before: dict[str, Any] | None, after: dict[str, Any] | None
) -> dict[str, dict[str, Any]]:
    """Flat per-path diff: ``{"path.to.field": {"from": ..., "to": ...}}``.

    Recurses into both dicts and lists so a single field changing inside
    ``variants[0].value.settings.welcome_message`` shows up as one path,
    not as a whole-``variants`` replacement.

    List recursion strategy:
      * If both sides are lists AND every element has a stable identifier
        (``system_name``, ``variant``, ``id``, or ``name`` in that order),
        align by that key. Indices in the path use the **before** position
        (or ``[+]`` for an added entry, ``[-]`` for a removed one).
      * Otherwise fall back to index-based comparison.
    """
    diff: dict[str, dict[str, Any]] = {}
    _diff_walk(before or {}, after or {}, prefix="", out=diff)
    return diff


_LIST_KEY_CANDIDATES: tuple[str, ...] = ("system_name", "variant", "id", "name")


def _list_key_field(before: list[Any], after: list[Any]) -> str | None:
    """Find the first identifier field present on EVERY element of both lists.

    Returns ``None`` when the lists contain scalars or heterogeneous shapes,
    in which case the caller falls back to index alignment.
    """
    items = [*before, *after]
    if not items or not all(isinstance(x, dict) for x in items):
        return None
    for key in _LIST_KEY_CANDIDATES:
        if all(key in x and x[key] is not None for x in items):
            return key
    return None


def _diff_walk(
    before: Any, after: Any, *, prefix: str, out: dict[str, dict[str, Any]]
) -> None:
    if before == after:
        return

    if isinstance(before, dict) and isinstance(after, dict):
        keys = set(before.keys()) | set(after.keys())
        for key in keys:
            child_prefix = f"{prefix}.{key}" if prefix else key
            _diff_walk(before.get(key), after.get(key), prefix=child_prefix, out=out)
        return

    if isinstance(before, list) and isinstance(after, list):
        key_field = _list_key_field(before, after)
        if key_field is not None:
            _diff_walk_keyed_list(before, after, key_field, prefix=prefix, out=out)
        else:
            _diff_walk_indexed_list(before, after, prefix=prefix, out=out)
        return

    out[prefix or "$"] = {"from": before, "to": after}


def _diff_walk_keyed_list(
    before: list[Any],
    after: list[Any],
    key_field: str,
    *,
    prefix: str,
    out: dict[str, dict[str, Any]],
) -> None:
    """Align list elements by ``key_field``, recurse per pair, mark add/remove."""
    by_key_before: dict[Any, tuple[int, Any]] = {
        item[key_field]: (idx, item) for idx, item in enumerate(before)
    }
    by_key_after: dict[Any, tuple[int, Any]] = {
        item[key_field]: (idx, item) for idx, item in enumerate(after)
    }
    seen: set[Any] = set()

    for key, (idx, item_before) in by_key_before.items():
        seen.add(key)
        if key in by_key_after:
            _, item_after = by_key_after[key]
            child_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            _diff_walk(item_before, item_after, prefix=child_prefix, out=out)
        else:
            child_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            out[child_prefix] = {"from": item_before, "to": None}

    for key, (idx, item_after) in by_key_after.items():
        if key in seen:
            continue
        # New entries don't have a "before" index — tag with the after index
        # so callers can still locate them in the new snapshot.
        child_prefix = f"{prefix}[+{idx}]" if prefix else f"[+{idx}]"
        out[child_prefix] = {"from": None, "to": item_after}


def _diff_walk_indexed_list(
    before: list[Any],
    after: list[Any],
    *,
    prefix: str,
    out: dict[str, dict[str, Any]],
) -> None:
    """Fallback: compare element-by-element at each index."""
    max_len = max(len(before), len(after))
    for idx in range(max_len):
        b = before[idx] if idx < len(before) else None
        a = after[idx] if idx < len(after) else None
        child_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
        _diff_walk(b, a, prefix=child_prefix, out=out)
