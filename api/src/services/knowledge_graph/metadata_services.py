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
    KnowledgeGraphDiscoveredMetadata,
    knowledge_graph_source_discovered_metadata_table,
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

    This performs a read-modify-write update on `KnowledgeGraphDiscoveredMetadata`:
    - creates missing fields (unique per graph_id + name)
    - increments `value_count` for each observed non-empty value
    - stores limited sample values (strings)
    - tracks origins (e.g. "source")

    Caller controls commit/rollback.
    """
    if not metadata:
        return

    origin_val = str(origin or "").strip() or None

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
                "name": name,
                "inferred_type": inferred_type,
                "origins": ([origin_val] if origin_val else None),
                "sample_values": sample_values,
                "value_count": value_count,
            }
        )

    if not rows:
        return

    max_sample_values_int = int(max_sample_values)
    if max_sample_values_int < 0:
        max_sample_values_int = 0

    insert_stmt = pg_insert(KnowledgeGraphDiscoveredMetadata).values(rows)
    excluded = insert_stmt.excluded
    cur = KnowledgeGraphDiscoveredMetadata

    empty_jsonb_array = literal("[]").cast(JSONB)

    inferred_type_expr = case(
        (cur.inferred_type.is_(None), excluded.inferred_type),
        (excluded.inferred_type.is_(None), cur.inferred_type),
        # Don't allow "unknown" to force a permanent "mixed" classification when we later infer a real type.
        (cur.inferred_type == literal("unknown"), excluded.inferred_type),
        (excluded.inferred_type == literal("unknown"), cur.inferred_type),
        (cur.inferred_type == excluded.inferred_type, cur.inferred_type),
        else_=literal("mixed"),
    )

    # Merge origins (best-effort unique, capped) without overwriting when excluded.origins is NULL.
    cur_origins = func.coalesce(cur.origins, empty_jsonb_array)
    exc_origins = func.coalesce(excluded.origins, empty_jsonb_array)
    origins_expr = case(
        # If incoming origins are NULL, keep existing as-is.
        (excluded.origins.is_(None), cur.origins),
        # If existing is NULL, take incoming.
        (cur.origins.is_(None), excluded.origins),
        # If already contains incoming, keep.
        (cur_origins.op("@>")(exc_origins), cur_origins),
        # Cap size to avoid unbounded growth.
        (func.jsonb_array_length(cur_origins) >= 10, cur_origins),
        # Append (arrays concatenate with ||)
        else_=cur_origins.op("||")(exc_origins),
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
              COALESCE(knowledge_graph_discovered_metadata.sample_values, '[]'::jsonb) ||
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
        index_elements=[cur.graph_id, cur.name],
        set_={
            # Aggregations
            "value_count": cur.value_count + excluded.value_count,
            "inferred_type": inferred_type_expr,
            "origins": origins_expr,
            "sample_values": samples_expr,
            # Audit
            "updated_at": func.now(),
        },
    )

    if source_id is None:
        await db_session.execute(stmt)
        return

    # Return ids so we can attribute fields to a specific source.
    res = await db_session.execute(stmt.returning(cur.id))

    discovered_ids = [r[0] for r in res.all() if r and r[0] is not None]
    if not discovered_ids:
        return

    assoc_rows = [
        {"source_id": source_id, "discovered_metadata_id": dm_id}
        for dm_id in discovered_ids
    ]
    assoc_insert = pg_insert(knowledge_graph_source_discovered_metadata_table).values(
        assoc_rows
    )
    assoc_insert = assoc_insert.on_conflict_do_nothing(
        index_elements=[
            knowledge_graph_source_discovered_metadata_table.c.source_id,
            knowledge_graph_source_discovered_metadata_table.c.discovered_metadata_id,
        ]
    )
    await db_session.execute(assoc_insert)
