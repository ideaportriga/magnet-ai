"""Filter compiler for knowledge graph entity records.

Translates the same filter expression syntax used for document metadata
filtering into SQL WHERE clauses targeting per-graph entity tables.

Field resolution:
- Known scalar columns (``entity``, ``record_identifier``, …) are compared
  directly against the table column.
- Known JSONB array columns (``identifier_aliases``, ``source_document_ids``,
  ``source_chunk_ids``) use array containment operators.
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
    "source_document_ids",
    "source_chunk_ids",
}


class EntityFilterCompiler(BaseFilterCompiler):
    """Compile filter expressions for a per-graph entity table."""

    def __init__(self, table_name: str) -> None:
        super().__init__()
        self._table = table_name

    def _compile_field_predicate(
        self, field_name: str, *, op: str, value: Any, values: Any
    ) -> str:
        if field_name in _SCALAR_COLUMNS:
            expr = f"{self._table}.{field_name}"
            return self._apply_scalar_op(expr, op=op, value=value, values=values)

        if field_name in _ARRAY_COLUMNS:
            expr = f"{self._table}.{field_name}"
            return self._apply_array_op(expr, op=op, value=value, values=values)

        # Fall through: treat as a key inside column_values JSONB.
        key_param = self.builder.add(field_name)
        expr = f"{self._table}.column_values ->> {key_param}"
        return self._apply_scalar_op(expr, op=op, value=value, values=values)
