"""
Knowledge Graph retrieval tool: `findDocumentsByMetadata`.

High-level purpose
------------------
The agentic retrieval flow often needs to narrow the search space before doing
embedding similarity search. For example: "only English docs", or "only Candidate
profiles", or "only docs where <field> contains <value>".

This tool compiles a structured *metadata filter expression* into:
- a SQL `WHERE` predicate (Postgres) that can be applied to the graph documents table
- a parameter dict for safe SQL binding (to avoid SQL injection)
- a count of how many documents match

Important behavioral detail
---------------------------
The agent (LLM) does *not* receive raw documents from this tool. The agent loop
only returns the **count** to the model, while keeping the generated SQL predicate
internally to constrain later chunk retrieval (`findChunksBySimilarity`).
"""

import json
import logging
from typing import Any, NamedTuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import docs_table_name
from services.observability import observability_context, observe
from services.observability.models import SpanType

from ....models import KnowledgeGraphRetrievalWorkflowStep

logger = logging.getLogger(__name__)

# Description of the `filter` parameter shown to the LLM.
# The value is a JSON-serialized expression language compiled by `_MetadataFilterCompiler`.
FILTER_PARAM_DESCRIPTION = (
    "Metadata filter expression serialized as a JSON string.\n"
    "Supports boolean groups {and/or/not} and predicates.\n\n"
    "Examples:\n"
    '  - {"field":"language_2l","op":"eq","value":"en"}\n'
    '  - {"and":[{"field":"language_2l","op":"in","values":["en","de"]},'
    '{"field":"candidate_name","op":"contains","value":"John"}]}\n'
    '  - {"path":["source","Candidate"],"op":"eq","value":"Alice"}\n\n'
    "Notes:\n"
    "- Use `field` for schema-defined metadata fields.\n"
    "- Use `path` to query raw metadata at [origin, key] where origin ∈ {source,file,llm}."
)

# OpenAI tool schema (sent to the LLM).
# `get_available_tools()` may tweak required params based on graph config (searchControl).
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "findDocumentsByMetadata",
        "description": "Filter documents by their metadata fields",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": (
                        "Why you are using this tool (e.g., 'Restricting to German documents')."
                    ),
                },
                "filter": {
                    "type": "string",
                    "description": FILTER_PARAM_DESCRIPTION,
                },
            },
            "required": ["reasoning", "filter"],
        },
    },
}


class FindDocumentsByMetadataToolResult(NamedTuple):
    """
    Result contract for `findDocumentsByMetadata` used by the retrieval agent loop.

    1) tool_payload: JSON-serializable content to send back to the LLM as the tool result
    2) loop_state: internal state the agent loop should keep for subsequent tool calls
    3) workflow_step: `KnowledgeGraphRetrievalWorkflowStep` to append to `workflow_steps`
    """

    tool_payload: dict[str, Any]
    loop_state: dict[str, Any]
    workflow_step: KnowledgeGraphRetrievalWorkflowStep


def _strip_surrounding_code_fences(value: Any) -> str:
    """
    Remove markdown code fences (e.g. ```json ... ```) often emitted by LLMs.
    """
    s = str(value or "").strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        if len(lines) >= 3:
            # Drop first line (```json) and last line (```)
            return "\n".join(lines[1:-1]).strip()
    return s


def _best_effort_json_value(value: Any) -> Any | None:
    """
    Parse a JSON object/array from either:
    - a dict/list already
    - a string (possibly code-fenced, or containing an embedded {...} / [...] region)

    Returns:
        dict/list if parsed and non-empty, otherwise None.
    """
    if isinstance(value, (dict, list)) and value:
        return value
    if not isinstance(value, str) or not value.strip():
        return None

    raw = _strip_surrounding_code_fences(value)
    if not raw:
        return None

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, (dict, list)) and parsed else None
    except Exception:
        pass

    # Heuristic: sometimes the LLM includes text outside the JSON block.
    # We attempt to find the outermost braces {} or brackets [] and parse that substring.
    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            parsed = json.loads(raw[first_brace : last_brace + 1])
            return parsed if isinstance(parsed, (dict, list)) and parsed else None
        except Exception:
            pass

    first_bracket = raw.find("[")
    last_bracket = raw.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        try:
            parsed = json.loads(raw[first_bracket : last_bracket + 1])
            return parsed if isinstance(parsed, (dict, list)) and parsed else None
        except Exception:
            pass

    return None


def _merge_filters(
    agent_raw: Any, external_raw: Any, *, merge_strategy: str
) -> Any | None:
    a_obj = _best_effort_json_value(agent_raw)
    b_obj = _best_effort_json_value(external_raw)

    merge_strategy = str(merge_strategy or "").strip().lower()
    if merge_strategy == "agent_priority":
        return a_obj or b_obj
    if merge_strategy == "external_priority":
        return b_obj or a_obj
    if merge_strategy == "merge_or":
        if a_obj and b_obj:
            return {"or": [b_obj, a_obj]}
        return a_obj or b_obj

    # default: merge_and
    if a_obj and b_obj:
        return {"and": [b_obj, a_obj]}
    return a_obj or b_obj


def _extract_external_metadata_filter(
    external_tool_inputs: dict[str, Any] | None,
) -> Any:
    """
    External tool inputs may supply the metadata filter in a couple shapes:
    - {"findDocumentsByMetadata": {"filter": <expr_or_str>}}
    - {"findDocumentsByMetadata": <expr_obj>}  (direct expression object)
    - {"findDocumentsByMetadata": "<json str>"} (direct string form)
    """
    ext_inputs = external_tool_inputs if isinstance(external_tool_inputs, dict) else {}
    ext_cfg = ext_inputs.get("findDocumentsByMetadata") if ext_inputs else None

    if isinstance(ext_cfg, dict):
        if "filter" in ext_cfg:
            return ext_cfg.get("filter")
        # Allow passing the filter expression directly as the tool input.
        return ext_cfg

    # Allow passing the filter expression directly as the tool input (string form).
    return ext_cfg


class _SqlParamBuilder:
    """Build SQL parameters with stable, unique names (p0, p1, ...) for safe binding."""

    def __init__(self) -> None:
        self.params: dict[str, Any] = {}
        self._idx = 0

    def add(self, value: Any) -> str:
        name = f"p{self._idx}"
        self._idx += 1
        self.params[name] = value
        return f":{name}"


class _MetadataFilterCompiler:
    """Compile a JSON metadata filter expression into SQL WHERE (Postgres).

    Supported expression forms (examples):

    - Boolean groups:
      - {"and": [expr, expr, ...]}
      - {"or": [expr, expr, ...]}
      - {"not": expr}

    - Field predicate (uses graph metadata field definitions + per-source resolution):
      - {"field": "language_2l", "op": "eq", "value": "en"}
      - {"field": "candidate_name", "op": "contains", "value": "John"}
      - {"field": "language_2l", "op": "in", "values": ["en", "de"]}

    - Raw predicate (bypass resolution; reads document metadata directly):
      - {"path": ["source", "Candidate"], "op": "eq", "value": "Alice"}
      - {"path": ["llm", "language_2l"], "op": "eq", "value": "en"}

    Notes:
    - `field` predicates are evaluated against the resolved value for each document's
      source using the configured `source_value_resolution` chain (fallback order).
    - If a field has no per-source chain configured, we fall back to checking the
      same key name across (source -> file -> llm).
    """

    def __init__(self, field_definitions: list[dict[str, Any]] | None) -> None:
        self.builder = _SqlParamBuilder()
        self.fields_by_name: dict[str, dict[str, Any]] = {}
        for fd in field_definitions or []:
            if not isinstance(fd, dict):
                continue
            name = str(fd.get("name") or "").strip()
            if not name:
                continue
            self.fields_by_name[name] = fd

    def compile(self, expr: Any) -> tuple[str, dict[str, Any]]:
        sql = self._compile_expr(expr)
        sql = str(sql or "").strip()
        return (sql, self.builder.params)

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
                return "TRUE"
            return "(" + " AND ".join(parts) + ")"

        if "or" in expr:
            items = expr.get("or")
            parts = [self._compile_expr(e) for e in (items or []) if e is not None]
            parts = [p for p in parts if p]
            if not parts:
                return "FALSE"
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

        if "path" in expr:
            path = expr.get("path")
            if not isinstance(path, list) or len(path) < 2:
                return ""
            origin = str(path[-2] or "").strip().lower()
            key = str(path[-1] or "").strip()
            if origin not in {"file", "source", "llm"} or not key:
                return ""
            return self._compile_raw_predicate(
                origin=origin,
                key=key,
                op=str(expr.get("op") or expr.get("operator") or "eq").strip().lower(),
                value=expr.get("value"),
                values=expr.get("values"),
            )

        return ""

    def _compile_raw_predicate(
        self, *, origin: str, key: str, op: str, value: Any, values: Any
    ) -> str:
        key_param = self.builder.add(key)
        # Normalize empty strings to NULL
        extracted = f"NULLIF(BTRIM(jsonb_extract_path_text(d.metadata, '{origin}', {key_param})), '')"
        return self._apply_scalar_op(extracted, op=op, value=value, values=values)

    def _compile_field_predicate(
        self, field_name: str, *, op: str, value: Any, values: Any
    ) -> str:
        fd = self.fields_by_name.get(field_name)
        if not fd:
            # Strict mode: only allow filtering on defined fields unless caller uses `path`.
            return "(1=0)"

        # Source-specific chain overrides
        # This allows a field like "author" to be resolved differently for "github" vs "slack" sources.
        chain_by_source: dict[str, list[dict[str, Any]]] = {}
        wildcard_chain: list[dict[str, Any]] | None = None

        def _normalize_chain(chain: list[Any]) -> list[dict[str, Any]]:
            """Normalize/defensively validate chain steps.

            - ensure kind is lowercased
            - ensure file/source/llm steps always have a field_name (fallback to schema field name)
            - keep constant payload as-is (validated later)
            """

            out: list[dict[str, Any]] = []
            for c in chain or []:
                if not isinstance(c, dict):
                    continue
                kind = str(c.get("kind") or "").strip().lower()
                if kind in {"file", "source", "llm"}:
                    fname = str(c.get("field_name") or "").strip() or field_name
                    out.append({"kind": kind, "field_name": fname})
                elif kind == "constant":
                    out.append(c)
            return out

        raw_resolutions = fd.get("source_value_resolution")
        if isinstance(raw_resolutions, list):
            for r in raw_resolutions:
                if not isinstance(r, dict):
                    continue
                sid = str(r.get("source_id") or "").strip()
                chain = r.get("chain")
                if not sid or not isinstance(chain, list) or not chain:
                    continue
                normalized = _normalize_chain(chain)
                if not normalized:
                    continue
                if sid == "*":
                    wildcard_chain = normalized
                else:
                    chain_by_source[sid] = normalized

        # Default chain when a source doesn't have an explicit mapping.
        # Best-effort: check same key name across origins.
        fallback_chain: list[dict[str, Any]] = (
            wildcard_chain
            if wildcard_chain is not None
            else [
                {"kind": "source", "field_name": field_name},
                {"kind": "file", "field_name": field_name},
                {"kind": "llm", "field_name": field_name},
            ]
        )

        # Compile per-source conditions, with a fallback for all other sources.
        parts: list[str] = []

        # (d.source_id::text = sid AND predicate(resolved(chain)))
        for sid, chain in chain_by_source.items():
            sid_param = self.builder.add(str(sid))
            resolved_expr = self._resolved_jsonb_array(chain)
            pred = self._apply_array_op(
                resolved_expr, op=op, value=value, values=values
            )
            parts.append(f"((d.source_id::text = {sid_param}) AND {pred})")

        # Fallback applies to docs whose source_id is not in the explicit mapping list.
        # This ensures that if a new source is added, we still attempt to find the metadata.
        resolved_fallback = self._resolved_jsonb_array(fallback_chain)
        pred_fallback = self._apply_array_op(
            resolved_fallback, op=op, value=value, values=values
        )

        if chain_by_source:
            # If we have source-specific logic, we must ensure the fallback logic only applies
            # to documents that DO NOT match any of those specific source IDs.
            mapped_sids = [self.builder.add(str(sid)) for sid in chain_by_source.keys()]
            guard = f"(d.source_id IS NULL OR d.source_id::text NOT IN ({', '.join(mapped_sids)}))"
            parts.append(f"({guard} AND {pred_fallback})")
        else:
            # No explicit source mapping: use fallback for all docs.
            parts.append(pred_fallback)

        return "(" + " OR ".join(parts) + ")"

    def _resolved_text(self, chain: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for step in chain or []:
            if not isinstance(step, dict):
                continue
            kind = str(step.get("kind") or "").strip().lower()
            if kind in {"file", "source", "llm"}:
                fname = str(step.get("field_name") or "").strip()
                if not fname:
                    continue
                key_param = self.builder.add(fname)
                parts.append(
                    "NULLIF(BTRIM(jsonb_extract_path_text(d.metadata, "
                    f"'{kind}', {key_param})), '')"
                )
            elif kind == "constant":
                const = step.get("constant_value")
                if const is None:
                    const_values = step.get("constant_values")
                    if isinstance(const_values, list) and const_values:
                        const = const_values[0]
                const_str = str(const).strip() if const is not None else ""
                if not const_str:
                    continue
                const_param = self.builder.add(const_str)
                parts.append(f"NULLIF(BTRIM({const_param}), '')")

        if not parts:
            return "NULL"
        if len(parts) == 1:
            return parts[0]
        return f"COALESCE({', '.join(parts)})"

    def _resolved_jsonb_array(self, chain: list[dict[str, Any]]) -> str:
        parts: list[str] = []

        def _as_nonempty_array(expr_jsonb: str) -> str:
            # Convert scalar -> array; treat empty arrays as NULL.
            arr = (
                f"CASE WHEN {expr_jsonb} IS NULL THEN NULL "
                f"WHEN jsonb_typeof({expr_jsonb}) = 'array' THEN {expr_jsonb} "
                f"ELSE jsonb_build_array({expr_jsonb}) END"
            )
            return (
                f"CASE WHEN {arr} IS NULL THEN NULL "
                f"WHEN jsonb_array_length({arr}) = 0 THEN NULL "
                f"ELSE {arr} END"
            )

        for step in chain or []:
            if not isinstance(step, dict):
                continue
            kind = str(step.get("kind") or "").strip().lower()
            if kind in {"file", "source", "llm"}:
                fname = str(step.get("field_name") or "").strip()
                if not fname:
                    continue
                key_param = self.builder.add(fname)
                raw = f"jsonb_extract_path(d.metadata, '{kind}', {key_param})"
                parts.append(_as_nonempty_array(raw))
            elif kind == "constant":
                const_values = step.get("constant_values")
                const_value = step.get("constant_value")
                values_list: list[Any] = []
                if isinstance(const_values, list) and const_values:
                    values_list = const_values
                elif const_value is not None and str(const_value).strip():
                    values_list = [const_value]
                if not values_list:
                    continue
                const_json = json.dumps(values_list, ensure_ascii=False, default=str)
                const_param = self.builder.add(const_json)
                raw = f"CAST({const_param} AS jsonb)"
                parts.append(_as_nonempty_array(raw))

        if not parts:
            return "NULL"
        if len(parts) == 1:
            return parts[0]
        return f"COALESCE({', '.join(parts)})"

    def _apply_scalar_op(self, expr: str, *, op: str, value: Any, values: Any) -> str:
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

        # Unsupported op -> never match
        return "(1=0)"

    def _apply_array_op(self, expr: str, *, op: str, value: Any, values: Any) -> str:
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


@observe(name="Find documents by metadata", type=SpanType.SEARCH)
async def findDocumentsByMetadata(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    args: dict[str, Any],
    iteration: int,
    tool_name: str = "findDocumentsByMetadata",
    tool_cfg: dict[str, Any] | None = None,
    external_tool_inputs: dict[str, Any] | None = None,
    field_definitions: list[dict[str, Any]] | None = None,
) -> FindDocumentsByMetadataToolResult:
    """
    Agent tool execution for `findDocumentsByMetadata`.

    This function purposely returns a 3-tuple used by the agent loop:
    1) Tool payload for the LLM (count only; never documents)
    2) Loop state updates (SQL predicate + params to constrain later chunk search)
    3) Workflow step for the API response

    The final filter used is determined by graph config:
    - searchControl: agent | external | collaborative
    - filterMergeStrategy: merge_and | merge_or | agent_priority | external_priority
    """

    logger.debug(f"Finding documents by metadata for graph {graph_id}")

    args = args if isinstance(args, dict) else {}
    tool_cfg_d = tool_cfg if isinstance(tool_cfg, dict) else {}

    search_control = str(tool_cfg_d.get("searchControl") or "agent").strip().lower()
    merge_strategy = (
        str(tool_cfg_d.get("filterMergeStrategy") or "merge_and").strip().lower()
    )

    ext_filter_raw = _extract_external_metadata_filter(external_tool_inputs)
    agent_filter_raw = args.get("filter")

    logger.debug(f"External filter: {ext_filter_raw}")
    logger.debug(f"Agent filter: {agent_filter_raw}")
    logger.debug(f"Search control: {search_control}")

    # Determine the final filter based on the configured control mode.
    # - "agent": The LLM controls the filter entirely.
    # - "external": The UI/API controls the filter (e.g. user selected a dropdown).
    # - "collaborative": We merge both (e.g. user says "only PDF" + LLM says "about AI").
    if search_control == "external":
        final_filter_obj = _best_effort_json_value(ext_filter_raw)
    elif search_control == "collaborative":
        final_filter_obj = _merge_filters(
            agent_filter_raw, ext_filter_raw, merge_strategy=merge_strategy
        )
    else:
        # agent
        final_filter_obj = _best_effort_json_value(agent_filter_raw)

    final_filter_str: str | None = None
    if final_filter_obj is not None:
        try:
            final_filter_str = json.dumps(
                final_filter_obj, ensure_ascii=False, default=str
            )
        except Exception:
            final_filter_str = None

    observability_context.update_current_span(
        input={"filter": final_filter_str},
    )

    # Compile + count
    # We execute a COUNT(*) query here so the LLM knows how many docs match its criteria.
    # We DO NOT return the actual documents to the LLM to save context window and latency.
    if final_filter_obj is None:
        count = 0
        where_sql = ""
        where_params: dict[str, Any] = {}
    else:
        compiler = _MetadataFilterCompiler(field_definitions)
        where_sql, params = compiler.compile(final_filter_obj)
        where_sql = str(where_sql or "").strip()
        where_params = dict(params or {})
        if not where_sql:
            count = 0
            where_sql = ""
            where_params = {}
        else:
            docs_tbl = docs_table_name(graph_id)
            sql = text(
                f"""
                SELECT COUNT(*)::bigint AS cnt
                FROM {docs_tbl} d
                WHERE d.status = 'completed'
                  AND ({where_sql})
                """
            )

            res = await db_session.execute(sql, dict(where_params))
            cnt = res.scalar_one_or_none()
            count = int(cnt or 0)

    doc_filter_where_sql: str | None = where_sql.strip() if where_sql.strip() else None
    doc_filter_where_params: dict[str, Any] | None = (
        where_params if doc_filter_where_sql is not None else None
    )

    observability_context.update_current_span(
        output={
            "count": count,
        }
    )

    tool_payload = {"matched_documents": count}
    loop_state = {
        "doc_filter_where_sql": doc_filter_where_sql,
        "doc_filter_where_params": doc_filter_where_params,
    }
    workflow_step = KnowledgeGraphRetrievalWorkflowStep(
        iteration=iteration,
        tool=tool_name,
        arguments={"filter": final_filter_str},
        call_summary={
            "reasoning": args.get("reasoning"),
            "result_count": count,
        },
    )

    return FindDocumentsByMetadataToolResult(
        tool_payload=tool_payload,
        loop_state=loop_state,
        workflow_step=workflow_step,
    )
