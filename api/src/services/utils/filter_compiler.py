"""Generic filter expression compiler for PostgreSQL.

Provides a reusable base for compiling JSON filter expressions into
parameterized SQL WHERE clauses. Subclasses implement field resolution
for their specific domain (e.g. document metadata, entity records).

Filter expression syntax:
    - Boolean groups:
        {"and": [expr, ...]}
        {"or": [expr, ...]}
        {"not": expr}

    - Field predicate:
        {"field": "name", "op": "eq", "value": "John"}
        {"field": "age", "op": "in", "values": [25, 30]}

    - Convenience: a bare list is treated as implicit AND.

Supported operators: eq, ne, in, contains, not_contains, like,
                     exists, not_exists, gt, gte, lt, lte
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SqlParamBuilder:
    """Build SQL parameters with stable, unique names (p0, p1, ...) for safe binding."""

    def __init__(self) -> None:
        self.params: dict[str, Any] = {}
        self._idx = 0

    def add(self, value: Any) -> str:
        name = f"p{self._idx}"
        self._idx += 1
        self.params[name] = value
        return f":{name}"


class BaseFilterCompiler(ABC):
    """Abstract base for compiling filter expressions to parameterized SQL.

    Subclasses must implement ``_compile_field_predicate`` to define how
    a field name is resolved to a SQL expression.
    """

    def __init__(self) -> None:
        self.builder = SqlParamBuilder()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self, expr: Any) -> tuple[str, dict[str, Any]]:
        """Compile *expr* and return ``(where_sql, params)``."""
        sql = self._compile_expr(expr)
        sql = str(sql or "").strip()
        return (sql, self.builder.params)

    # ------------------------------------------------------------------
    # Expression dispatch (boolean + leaf)
    # ------------------------------------------------------------------

    def _compile_expr(self, expr: Any) -> str:
        # Convenience: a list is treated as an implicit AND group
        if isinstance(expr, list):
            return self._compile_expr({"and": expr})

        if not isinstance(expr, dict):
            return ""

        if "and" in expr:
            items = expr.get("and")
            parts = [self._compile_expr(e) for e in (items or []) if e is not None]
            parts = [p for p in parts if p]
            if not parts:
                return ""
            return "(" + " AND ".join(parts) + ")"

        if "or" in expr:
            items = expr.get("or")
            parts = [self._compile_expr(e) for e in (items or []) if e is not None]
            parts = [p for p in parts if p]
            if not parts:
                return ""
            return "(" + " OR ".join(parts) + ")"

        if "not" in expr:
            inner = self._compile_expr(expr.get("not"))
            if not inner:
                return ""
            return f"(NOT ({inner}))"

        # Leaf predicates
        if "field" in expr:
            field = str(expr.get("field") or "").strip()
            if not field:
                return ""
            return self._compile_field_predicate(
                field,
                op=str(expr.get("op") or expr.get("operator") or "eq").strip().lower(),
                value=expr.get("value"),
                values=expr.get("values"),
            )

        return ""

    # ------------------------------------------------------------------
    # Abstract: subclass must provide field resolution
    # ------------------------------------------------------------------

    @abstractmethod
    def _compile_field_predicate(
        self, field_name: str, *, op: str, value: Any, values: Any
    ) -> str:
        """Compile a leaf field predicate into a SQL fragment."""
        ...

    # ------------------------------------------------------------------
    # Reusable operator helpers
    # ------------------------------------------------------------------

    def _apply_scalar_op(self, expr: str, *, op: str, value: Any, values: Any) -> str:
        """Apply an operator to a scalar SQL expression (text column or JSONB ->> path)."""
        op = (op or "eq").strip().lower()

        if op in {"exists", "is_set"}:
            return f"({expr} IS NOT NULL)"
        if op in {"not_exists", "is_not_set"}:
            return f"({expr} IS NULL)"

        if op in {"in"}:
            vals = values
            if vals is None:
                vals = value
            if not isinstance(vals, list):
                return self._apply_scalar_op(expr, op="eq", value=value, values=None)
            sub = []
            for v in vals:
                if v is None:
                    sub.append(f"({expr} IS NULL)")
                else:
                    p = self.builder.add(str(v))
                    sub.append(f"({expr} = {p})")
            if not sub:
                return "(1=0)"
            return "(" + " OR ".join(sub) + ")"

        if op in {"contains", "like"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} ILIKE '%' || {p} || '%')"

        if op in {"not_contains"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} NOT ILIKE '%' || {p} || '%')"

        if op in {"eq", "=", "=="}:
            if value is None:
                return f"({expr} IS NULL)"
            p = self.builder.add(str(value))
            return f"({expr} = {p})"

        if op in {"ne", "!=", "<>"}:
            if value is None:
                return f"({expr} IS NOT NULL)"
            p = self.builder.add(str(value))
            return f"({expr} <> {p})"

        if op in {"gt", ">"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} > {p})"

        if op in {"gte", ">="}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} >= {p})"

        if op in {"lt", "<"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} < {p})"

        if op in {"lte", "<="}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return f"({expr} <= {p})"

        # Unsupported op -> never match
        return "(1=0)"

    def _apply_array_op(self, expr: str, *, op: str, value: Any, values: Any) -> str:
        """Apply an operator to a JSONB array SQL expression."""
        op = (op or "eq").strip().lower()
        expr_sql = f"({expr})"

        if op in {"exists", "is_set"}:
            return f"({expr_sql} IS NOT NULL)"
        if op in {"not_exists", "is_not_set"}:
            return f"({expr_sql} IS NULL)"

        def _exists(where_sql: str) -> str:
            return (
                f"({expr_sql} IS NOT NULL AND EXISTS ("
                f"SELECT 1 FROM jsonb_array_elements_text({expr_sql}) AS e(val) "
                f"WHERE {where_sql}"
                f"))"
            )

        if op in {"in"}:
            vals = values
            if vals is None:
                vals = value
            if not isinstance(vals, list):
                return self._apply_array_op(expr, op="eq", value=value, values=None)
            sub: list[str] = []
            if any(v is None for v in vals):
                sub.append(f"({expr_sql} IS NULL)")
            for v in vals:
                if v is None:
                    continue
                p = self.builder.add(str(v))
                sub.append(_exists(f"e.val = {p}"))
            if not sub:
                return "(1=0)"
            return "(" + " OR ".join(sub) + ")"

        if op in {"eq", "=", "==", "has"}:
            if value is None:
                return f"({expr_sql} IS NULL)"
            p = self.builder.add(str(value))
            return _exists(f"e.val = {p}")

        if op in {"contains", "like"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return _exists(f"e.val ILIKE '%' || {p} || '%'")

        if op in {"ne", "!=", "<>"}:
            if value is None:
                return f"({expr_sql} IS NOT NULL)"
            p = self.builder.add(str(value))
            return (
                f"({expr_sql} IS NOT NULL AND NOT EXISTS ("
                f"SELECT 1 FROM jsonb_array_elements_text({expr_sql}) AS e(val) "
                f"WHERE e.val = {p}"
                f"))"
            )

        if op in {"not_contains"}:
            if value is None:
                return "(1=0)"
            p = self.builder.add(str(value))
            return (
                f"({expr_sql} IS NOT NULL AND NOT EXISTS ("
                f"SELECT 1 FROM jsonb_array_elements_text({expr_sql}) AS e(val) "
                f"WHERE e.val ILIKE '%' || {p} || '%'"
                f"))"
            )

        return "(1=0)"
