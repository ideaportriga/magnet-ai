from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, literal, literal_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphMetadataDiscovery,
)

from .models import MetadataMultiValueContainer

logger = logging.getLogger(__name__)

_DEFAULT_MAX_SAMPLE_VALUES = 10
_DEFAULT_MAX_SAMPLE_CHARS = 256


def _is_simple_scalar(value: Any) -> bool:
    # Best-effort: allow common scalar types; reject structured containers.
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if isinstance(value, (datetime, date)):
        return True
    if isinstance(value, UUID):
        return True
    if isinstance(value, str):
        return True
    return False


def _extract_indexed_mapping_values(value: Any) -> list[Any] | None:
    """Extract values from list-like dicts with numeric keys.

    Example: {0: "A", 1: "B"} or {"0": "A", "1": "B"} -> ["A", "B"]
    """
    if not isinstance(value, dict) or not value:
        return None

    items: list[tuple[int, Any]] = []
    for k, v in value.items():
        if isinstance(k, int):
            idx = k
        elif isinstance(k, str) and k.strip().isdigit():
            idx = int(k.strip())
        else:
            return None
        items.append((idx, v))

    if not items or not all(_is_simple_scalar(v) for _, v in items):
        return None

    items.sort(key=lambda t: t[0])
    return [v for _, v in items]


def _infer_metadata_value_type(value: Any) -> str:
    if isinstance(value, MetadataMultiValueContainer):
        # Infer from contained values; ignore "unknown" unless it's the only type.
        types = {_infer_metadata_value_type(v) for v in value.values if v is not None}
        types.discard("unknown")
        if not types:
            return "unknown"
        if len(types) == 1:
            return next(iter(types))
        return "mixed"
    indexed_values = _extract_indexed_mapping_values(value)
    if indexed_values is not None:
        return _infer_metadata_value_type(
            MetadataMultiValueContainer.from_iterable(indexed_values)
        )
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, (datetime, date)):
        return "date"
    if isinstance(value, (list, tuple, set)):
        return "unknown"
    if isinstance(value, dict):
        return "unknown"
    return "string"


def _stringify_metadata_value(value: Any, *, max_chars: int) -> str | None:
    """Best-effort conversion of a metadata value to a short string."""
    if value is None:
        return None

    # Drop empty strings early
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        return s[:max_chars]

    if isinstance(value, (datetime, date)):
        return value.isoformat()[:max_chars]

    # Simple scalars
    if isinstance(value, (bool, int, float)):
        return str(value)[:max_chars]

    # Structured values: prefer JSON, fallback to str()
    try:
        s = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        s = str(value)

    s = str(s).strip()
    if not s:
        return None
    return s[:max_chars]


def _extract_sample_values_and_count(
    value: Any, *, max_chars: int, max_sample_values: int
) -> tuple[list[str], int]:
    """Return (sample_values, value_count_increment) for a single metadata field."""
    max_sample_values = int(max_sample_values)
    if max_sample_values < 0:
        max_sample_values = 0

    if isinstance(value, MetadataMultiValueContainer):
        samples: list[str] = []
        seen: set[str] = set()
        count = 0
        for v in value.values:
            s = _stringify_metadata_value(v, max_chars=max_chars)
            if s is None:
                continue
            count += 1
            if max_sample_values == 0 or len(samples) >= max_sample_values:
                continue
            if s in seen:
                continue
            seen.add(s)
            samples.append(s)
        return samples, count

    indexed_values = _extract_indexed_mapping_values(value)
    if indexed_values is not None:
        return _extract_sample_values_and_count(
            MetadataMultiValueContainer.from_iterable(indexed_values),
            max_chars=max_chars,
            max_sample_values=max_sample_values,
        )

    sample = _stringify_metadata_value(value, max_chars=max_chars)
    if sample is None:
        return [], 0
    return [sample], 1


async def accumulate_discovered_metadata_fields(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    source_id: UUID | None = None,
    metadata: dict[str, Any],
    origin: str = "source",
    max_sample_values: int = _DEFAULT_MAX_SAMPLE_VALUES,
    max_sample_chars: int = _DEFAULT_MAX_SAMPLE_CHARS,
) -> None:
    """Accumulate discovered metadata fields for a knowledge graph (best-effort).

    This performs a read-modify-write update on `KnowledgeGraphMetadataDiscovery`:
    - creates missing fields (unique per source_id + name)
    - increments `value_count` for each observed non-empty value
    - stores limited sample values (strings)
    - tracks origin (file/source/llm)

    Caller controls commit/rollback.
    """
    if not metadata:
        return

    if source_id is None:
        # 1:M model requires attribution to a single source.
        return

    origin_val = str(origin or "").strip().lower()
    if origin_val == "document":
        # Back-compat alias for "file"
        origin_val = "file"
    if origin_val not in ("file", "source", "llm"):
        origin_val = None

    rows: list[dict[str, Any]] = []
    for raw_name, value in metadata.items():
        name = str(raw_name or "").strip()
        if not name:
            continue

        inferred_type = _infer_metadata_value_type(value)
        sample_values, value_count = _extract_sample_values_and_count(
            value, max_chars=max_sample_chars, max_sample_values=max_sample_values
        )

        # We only "count" fields that have an actual value
        if not sample_values or value_count <= 0:
            continue

        rows.append(
            {
                "graph_id": graph_id,
                "source_id": source_id,
                "name": name,
                "inferred_type": inferred_type,
                "origin": origin_val,
                "sample_values": sample_values,
                "value_count": value_count,
            }
        )

    if not rows:
        return

    max_sample_values_int = int(max_sample_values)
    if max_sample_values_int < 0:
        max_sample_values_int = 0

    insert_stmt = pg_insert(KnowledgeGraphMetadataDiscovery).values(rows)
    excluded = insert_stmt.excluded
    cur = KnowledgeGraphMetadataDiscovery

    inferred_type_expr = case(
        (cur.inferred_type.is_(None), excluded.inferred_type),
        (excluded.inferred_type.is_(None), cur.inferred_type),
        # Don't allow "unknown" to force a permanent "mixed" classification when we later infer a real type.
        (cur.inferred_type == literal("unknown"), excluded.inferred_type),
        (excluded.inferred_type == literal("unknown"), cur.inferred_type),
        (cur.inferred_type == excluded.inferred_type, cur.inferred_type),
        else_=literal("mixed"),
    )

    # Merge sample values (unique-ish, capped).
    # Note: excluded.sample_values may contain multiple items (e.g., from MetadataMultiValueContainer).
    # NOTE: We intentionally rebuild `sample_values` as a deduped union of
    # (existing || incoming) on every update to guarantee uniqueness even if
    # duplicates already exist in the DB.
    #
    # We preserve "first seen" order using WITH ORDINALITY over the concatenated
    # array: existing values keep priority; new values are appended.
    if max_sample_values_int <= 0:
        # Match prior behavior: never grow the samples list once present; only set it
        # on first insert (when current is NULL).
        samples_expr = case(
            (excluded.sample_values.is_(None), cur.sample_values),
            else_=func.coalesce(cur.sample_values, excluded.sample_values),
        )
    else:
        cap_path_str = f"$[0 to {max(0, max_sample_values_int - 1)}]"
        # This subquery:
        # - concatenates existing + incoming samples
        # - assigns ordinality (position) across the concatenation
        # - keeps the earliest occurrence per distinct value
        # - aggregates back into a JSONB array ordered by first occurrence
        # - caps to max_sample_values
        samples_union_dedup_sql = f"""
        (
          SELECT jsonb_path_query_array(
            COALESCE(jsonb_agg(val ORDER BY ord), '[]'::jsonb),
            '{cap_path_str}'::jsonpath
          )
          FROM (
            SELECT value AS val, MIN(ord) AS ord
            FROM jsonb_array_elements_text(
              COALESCE(knowledge_graph_metadata_discoveries.sample_values, '[]'::jsonb) ||
              COALESCE(excluded.sample_values, '[]'::jsonb)
            ) WITH ORDINALITY AS t(value, ord)
            GROUP BY value
            ORDER BY MIN(ord)
          ) u
        )
        """
        samples_expr = case(
            (excluded.sample_values.is_(None), cur.sample_values),
            else_=literal_column(samples_union_dedup_sql).cast(JSONB),
        )

    stmt = insert_stmt.on_conflict_do_update(
        index_elements=[cur.graph_id, cur.source_id, cur.origin, cur.name],
        set_={
            # Aggregations
            "value_count": cur.value_count + excluded.value_count,
            "inferred_type": inferred_type_expr,
            "sample_values": samples_expr,
            # Audit
            "updated_at": func.now(),
        },
    )

    await db_session.execute(stmt)
