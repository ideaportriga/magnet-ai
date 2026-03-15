"""Filter compiler for knowledge graph entity records.

Translates the same filter expression syntax used for document metadata
filtering into SQL WHERE clauses targeting per-graph entity tables.

Field resolution:
- Known scalar columns (``entity``, ``record_identifier``, …) are compared
  directly against the table column.
- Known JSONB array columns (``identifier_aliases``) use array containment
  operators.
- Edge-backed fields (``source_document_ids``, ``source_chunk_ids``) are
  resolved via EXISTS subqueries against the per-graph edges table.
- Any other field name is treated as a key inside the ``column_values`` JSONB
  column (flat key lookup via ``->>``).
"""

from __future__ import annotations

from typing import Any

from services.utils.filter_compiler import BaseFilterCompiler

# Columns that map directly to a VARCHAR / TIMESTAMP column on the entity table.
_SCALAR_COLUMNS: set[str] = {
    "entity",
    "record_identifier",
    "normalized_record_identifier",
    "created_at",
    "updated_at",
}

# Columns stored as JSONB arrays.
_ARRAY_COLUMNS: set[str] = {
    "identifier_aliases",
}

# Fields backed by the edges table. Maps field name -> target_node_type.
_EDGE_FIELDS: dict[str, str] = {
    "source_document_ids": "document",
    "source_chunk_ids": "chunk",
}


class EntityFilterCompiler(BaseFilterCompiler):
    """Compile filter expressions for a per-graph entity table."""

    def __init__(self, table_name: str, edges_table_name: str | None = None) -> None:
        super().__init__()
        self._table = table_name
        self._edges_table = edges_table_name

    def _compile_field_predicate(
        self, field_name: str, *, op: str, value: Any, values: Any
    ) -> str:
        if field_name in _SCALAR_COLUMNS:
            expr = f"{self._table}.{field_name}"
            return self._apply_scalar_op(expr, op=op, value=value, values=values)

        if field_name in _ARRAY_COLUMNS:
            expr = f"{self._table}.{field_name}"
            return self._apply_array_op(expr, op=op, value=value, values=values)

        if field_name in _EDGE_FIELDS and self._edges_table:
            target_type = _EDGE_FIELDS[field_name]
            return self._apply_edge_filter(
                target_type, op=op, value=value, values=values
            )

        # Fall through: treat as a key inside column_values JSONB.
        key_param = self.builder.add(field_name)
        expr = f"{self._table}.column_values ->> {key_param}"
        return self._apply_scalar_op(expr, op=op, value=value, values=values)

    def _apply_edge_filter(
        self, target_type: str, *, op: str, value: Any, values: Any
    ) -> str:
        """Generate EXISTS / NOT EXISTS subqueries against the edges table."""
        op = (op or "eq").strip().lower()
        et = self._edges_table
        tbl = self._table
        tp = self.builder.add(target_type)

        def _exists_sql(where_fragment: str) -> str:
            return (
                f"EXISTS (SELECT 1 FROM {et} e "
                f"WHERE e.source_node_id = {tbl}.id "
                f"AND e.source_node_type = 'entity' "
                f"AND e.target_node_type = {tp} "
                f"AND {where_fragment})"
            )

        def _not_exists_sql(where_fragment: str) -> str:
            return (
                f"NOT EXISTS (SELECT 1 FROM {et} e "
                f"WHERE e.source_node_id = {tbl}.id "
                f"AND e.source_node_type = 'entity' "
                f"AND e.target_node_type = {tp} "
                f"AND {where_fragment})"
            )

        if op in {"exists", "is_set"}:
            return _exists_sql("1=1")

        if op in {"not_exists", "is_not_set"}:
            return _not_exists_sql("1=1")

        if op in {"eq", "=", "==", "has"}:
            if value is None:
                return _not_exists_sql("1=1")
            p = self.builder.add(str(value))
            return _exists_sql(f"e.target_node_id::text = {p}")

        if op in {"ne", "!=", "<>"}:
            if value is None:
                return _exists_sql("1=1")
            p = self.builder.add(str(value))
            return _not_exists_sql(f"e.target_node_id::text = {p}")

        if op in {"in"}:
            vals = (
                values
                if isinstance(values, list)
                else ([value] if value is not None else [])
            )
            if not vals:
                return "(1=0)"
            sub: list[str] = []
            for v in vals:
                if v is None:
                    continue
                p = self.builder.add(str(v))
                sub.append(_exists_sql(f"e.target_node_id::text = {p}"))
            if not sub:
                return "(1=0)"
            return "(" + " OR ".join(sub) + ")"

        if op in {"contains", "like"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return _exists_sql(f"e.target_node_id::text ILIKE '%' || {p} || '%'")

        if op in {"not_contains"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return _not_exists_sql(f"e.target_node_id::text ILIKE '%' || {p} || '%'")

        return "(1=0)"
