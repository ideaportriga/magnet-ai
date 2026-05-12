from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    chunks_table_name,
    docs_table_name,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphEntityExtractionRunRequest,
)
from core.domain.knowledge_graph.services.knowledge_graph_entity_service import (
    KnowledgeGraphEntityService,
    normalize_record_identifier,
)
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from utils.datetime_utils import utc_now_isoformat

logger = logging.getLogger(__name__)

# Registry of actively running extraction tasks keyed by graph_id.
# Used to distinguish a live running process from a stale "running" DB status
# (e.g. after a backend restart).
_active_extraction_tasks: dict[UUID, bool] = {}

EntityExtractionApproach = Literal["document", "chunks"]
EntityExtractionMode = Literal["basic", "advanced", "reflective"]
EXTRACTION_MODES: tuple[str, ...] = ("basic", "advanced", "reflective")
DEFAULT_EXTRACTION_MODE: EntityExtractionMode = "basic"
EntityColumnType = Literal["string", "number", "boolean", "date"]
EntityExtractionSchemaFormat = Literal["json_schema", "typescript", "markdown"]
SCHEMA_FORMATS: tuple[str, ...] = ("json_schema", "typescript", "markdown")
DEFAULT_SCHEMA_FORMAT: EntityExtractionSchemaFormat = "typescript"
_JSON_SCHEMA_MODE_PROMPT_HINT = (
    "The schema for the entity records is provided as a JSON Schema attached to "
    "this request as the `response_format`. Follow it exactly."
)
_JSON_SCHEMA_MODE_PROMPT_HINT_REFLECTIVE = (
    "The schema for your output (a top-level object with `analysis` and `records` "
    "fields) is provided as a JSON Schema attached to this request as the "
    "`response_format`. Follow it exactly."
)


@dataclass(slots=True)
class EntityColumnDefinition:
    name: str
    description: str = ""
    type: EntityColumnType = "string"
    is_identifier: bool = False
    is_required: bool = False


@dataclass(slots=True)
class EntityDefinition:
    name: str
    description: str = ""
    columns: list[EntityColumnDefinition] | None = None
    identifier_column: str = ""


@dataclass(slots=True)
class EntityCandidateRecord:
    entity: str
    record_identifier: str
    column_values: dict[str, Any]


# Hard cap on the few-shot example bank produced by the analysis pass.
# The analysis prompt also asks for at most this many examples; the cap is
# enforced post-parse defensively in case the model exceeds it.
MAX_ANALYSIS_EXAMPLES = 3


@dataclass(slots=True)
class AnalysisEnvelope:
    """Parsed output of the AdvancedStrategy analysis pass."""

    segment_overview: str
    global_context: dict[str, str]
    examples: list[dict[str, Any]]


def _empty_global_context() -> dict[str, str]:
    return {
        "shared_values": "",
        "schema_observations": "",
        "disambiguation_rules": "",
    }


def normalize_entity_definitions(
    entity_definitions: list[dict[str, Any]] | list[EntityDefinition] | Any,
) -> list[EntityDefinition]:
    if not isinstance(entity_definitions, list):
        raise ValueError("entity_definitions must be a list")

    normalized_entities: list[EntityDefinition] = []
    seen_entities: set[str] = set()

    for raw_entity in entity_definitions:
        if isinstance(raw_entity, EntityDefinition):
            entity_name = str(raw_entity.name or "").strip()
            entity_description = str(raw_entity.description or "").strip()
            raw_columns = raw_entity.columns or []
        elif isinstance(raw_entity, dict):
            if raw_entity.get("enabled") is False:
                continue
            entity_name = str(raw_entity.get("name") or "").strip()
            entity_description = str(raw_entity.get("description") or "").strip()
            raw_columns = (
                raw_entity.get("columns")
                if isinstance(raw_entity.get("columns"), list)
                else []
            )
        else:
            continue

        if not entity_name:
            continue

        entity_key = entity_name.casefold()
        if entity_key in seen_entities:
            raise ValueError(f"Duplicate entity definition: {entity_name}")
        seen_entities.add(entity_key)

        columns: list[EntityColumnDefinition] = []
        seen_columns: set[str] = set()
        identifier_columns: list[str] = []

        for raw_column in raw_columns:
            if isinstance(raw_column, EntityColumnDefinition):
                column_name = str(raw_column.name or "").strip()
                column_description = str(raw_column.description or "").strip()
                column_type = str(raw_column.type or "string").strip().lower()
                is_identifier = bool(raw_column.is_identifier)
                is_required = bool(raw_column.is_required)
            elif isinstance(raw_column, dict):
                column_name = str(raw_column.get("name") or "").strip()
                column_description = str(raw_column.get("description") or "").strip()
                column_type = str(raw_column.get("type") or "string").strip().lower()
                is_identifier = bool(raw_column.get("is_identifier"))
                is_required = bool(raw_column.get("is_required"))
            else:
                continue

            if not column_name:
                continue

            column_key = column_name.casefold()
            if column_key in seen_columns:
                raise ValueError(
                    f"Duplicate column '{column_name}' in entity '{entity_name}'"
                )
            seen_columns.add(column_key)

            if column_type not in {"string", "number", "boolean", "date"}:
                column_type = "string"

            columns.append(
                EntityColumnDefinition(
                    name=column_name,
                    description=column_description,
                    type=column_type,  # type: ignore[arg-type]
                    is_identifier=is_identifier,
                    is_required=is_required,
                )
            )
            if is_identifier:
                identifier_columns.append(column_name)

        if not columns:
            raise ValueError(f"Entity '{entity_name}' must define at least one column")
        if len(identifier_columns) != 1:
            raise ValueError(
                f"Entity '{entity_name}' must define exactly one identifier column"
            )

        normalized_entities.append(
            EntityDefinition(
                name=entity_name,
                description=entity_description,
                columns=columns,
                identifier_column=identifier_columns[0],
            )
        )

    if not normalized_entities:
        raise ValueError("At least one entity definition is required")

    return normalized_entities


def build_entity_extraction_prompt_schema_typescript(
    entity_definitions: list[EntityDefinition],
    *,
    include_analysis: bool = False,
) -> str:
    has_required_fields = any(
        col.is_required for ed in entity_definitions for col in (ed.columns or [])
    )
    lines: list[str] = []
    if has_required_fields:
        lines += [
            "/**",
            " * Field notation:",
            " *   field: type        — REQUIRED. If this field cannot be extracted, do NOT include the record at all.",
            " *   field?: type | null — Optional. Omit or set to null if not found.",
            " */",
        ]
    lines.append("type ExtractedEntityRecords = {")
    if include_analysis:
        lines.append(
            "  /** Updated running analysis of the document (plain text). Required. */"
        )
        lines.append("  analysis: string")
        lines.append("")
    ts_type_map: dict[EntityColumnType, str] = {
        "string": "string",
        "number": "number",
        "boolean": "boolean",
        "date": "string",
    }

    for entity_definition in entity_definitions:
        lines.append("  /**")
        lines.append(
            f"   * Entity: {entity_definition.name}; Identifier column: {entity_definition.identifier_column}"
        )
        if entity_definition.description:
            for description_line in entity_definition.description.splitlines():
                lines.append(f"   * {description_line}".rstrip())
        lines.append("   */")
        lines.append("  records: Array<{")

        for column in entity_definition.columns or []:
            comment_parts = [f"Type: {column.type}"]
            if column.is_identifier:
                comment_parts.append("Primary identifier")
            if column.description:
                comment_parts.append(column.description)
            lines.append(f"    /** {'; '.join(comment_parts)} */")
            if column.is_required:
                lines.append(
                    f"    {json.dumps(column.name)}: {ts_type_map[column.type]}"
                )
            else:
                lines.append(
                    f"    {json.dumps(column.name)}?: {ts_type_map[column.type]} | null"
                )

        lines.append("  }>")
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    lines.append("}")
    return "\n".join(lines).strip() + "\n"


_MARKDOWN_TYPE_LABEL: dict[EntityColumnType, str] = {
    "string": "string",
    "number": "number",
    "boolean": "boolean",
    "date": "date (ISO 8601)",
}


def build_entity_extraction_prompt_schema_markdown(
    entity_definitions: list[EntityDefinition],
    *,
    include_analysis: bool = False,
) -> str:
    """Render the entity schema as a simple markdown listing.

    Mentions every entity, its identifier column, every column with its type
    and required/optional flag, and any column description.
    """
    blocks: list[str] = []
    if include_analysis:
        blocks.append(
            "### Output\n"
            "Return a JSON object with two top-level fields:\n"
            "- `analysis` (string, required) — running document analysis (plain text).\n"
            "- `records` (array, required) — extracted records of the entity below."
        )
    for entity_definition in entity_definitions:
        lines: list[str] = []
        identifier = entity_definition.identifier_column
        header = f"### {entity_definition.name}"
        lines.append(header)
        lines.append(f"- Identifier column: `{identifier}`")
        description = (entity_definition.description or "").strip()
        if description:
            for description_line in description.splitlines():
                stripped = description_line.strip()
                if stripped:
                    lines.append(f"- {stripped}")
        lines.append("- Columns:")
        for column in entity_definition.columns or []:
            type_label = _MARKDOWN_TYPE_LABEL.get(column.type, column.type)
            requirement = "required" if column.is_required else "optional"
            tags = [type_label, requirement]
            if column.is_identifier:
                tags.append("identifier")
            tag_str = ", ".join(tags)
            column_description = (column.description or "").strip().replace("\n", " ")
            if column_description:
                lines.append(f"  - `{column.name}` ({tag_str}) — {column_description}")
            else:
                lines.append(f"  - `{column.name}` ({tag_str})")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks).rstrip() + "\n"


_JSON_SCHEMA_TYPE_MAP: dict[EntityColumnType, str] = {
    "string": "string",
    "number": "number",
    "boolean": "boolean",
    "date": "string",
}


def _build_entity_record_item_schema(
    entity_definition: EntityDefinition,
) -> dict[str, Any]:
    item_properties: dict[str, Any] = {}
    item_required: list[str] = []
    for column in entity_definition.columns or []:
        json_type = _JSON_SCHEMA_TYPE_MAP.get(column.type, "string")
        column_schema: dict[str, Any] = (
            {"type": json_type} if column.is_required else {"type": [json_type, "null"]}
        )
        if column.type == "date":
            column_schema["description"] = "ISO 8601 date (YYYY-MM-DD)"
        if column.description:
            existing_description = column_schema.get("description")
            column_schema["description"] = (
                f"{existing_description}. {column.description}"
                if existing_description
                else column.description
            )
        item_properties[column.name] = column_schema
        # In OpenAI strict structured outputs every property must be in `required`;
        # optional fields are expressed via the `["<type>", "null"]` type union.
        item_required.append(column.name)

    return {
        "type": "object",
        "properties": item_properties,
        "required": item_required,
        "additionalProperties": False,
    }


def build_entity_extraction_prompt_schema_json(
    entity_definition: EntityDefinition,
    *,
    include_analysis: bool = False,
) -> dict[str, Any]:
    """Build a strict JSON Schema describing the records output for a single entity.

    Shape::

        {"records": [{<column>: <value>, ...}, ...]}

    With ``include_analysis=True`` the schema additionally requires an
    ``analysis`` string field at the top level — used by the reflective strategy.
    """
    item_schema = _build_entity_record_item_schema(entity_definition)

    properties: dict[str, Any] = {}
    required: list[str] = []
    if include_analysis:
        properties["analysis"] = {
            "type": "string",
            "description": (
                "Running document analysis. Plain text; carries forward to the "
                "next segment as cross-segment context."
            ),
        }
        required.append("analysis")
    properties["records"] = {
        "type": "array",
        "items": item_schema,
    }
    required.append("records")

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def build_entity_extraction_response_format(
    entity_definition: EntityDefinition,
    *,
    include_analysis: bool = False,
) -> dict[str, Any]:
    """Build the OpenAI structured-output `response_format` for json_schema mode."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": (
                "kg_entity_extraction_reflective_response"
                if include_analysis
                else "kg_entity_extraction_response"
            ),
            "schema": build_entity_extraction_prompt_schema_json(
                entity_definition, include_analysis=include_analysis
            ),
            "strict": True,
        },
    }


def build_entity_schema_summary(
    entity_definitions: list[EntityDefinition],
) -> str:
    """Compact markdown summary of the entity schema for the analysis prompt.

    Drops types and required/optional notation — the analysis pass only needs
    to know which entities exist, what their identifier is, and what columns
    must be filled.
    """
    lines: list[str] = []
    for entity_definition in entity_definitions:
        identifier = entity_definition.identifier_column
        header = f"- **{entity_definition.name}** (identifier: `{identifier}`)"
        if entity_definition.description:
            description_first_line = entity_definition.description.splitlines()[
                0
            ].strip()
            if description_first_line:
                header = f"{header} — {description_first_line}"
        lines.append(header)

        for column in entity_definition.columns or []:
            tag = " *(identifier)*" if column.is_identifier else ""
            description = (column.description or "").strip().replace("\n", " ")
            if description:
                lines.append(f"  - `{column.name}`{tag} — {description}")
            else:
                lines.append(f"  - `{column.name}`{tag}")

    return "\n".join(lines)


def _strip_surrounding_code_fences(value: str) -> str:
    if not value:
        return value
    match = re.match(r"^\s*```[^\n]*\n([\s\S]*?)\n?\s*```\s*$", value, flags=re.DOTALL)
    return match.group(1).strip() if match else value.strip()


def _best_effort_json_object_from_text(value: str) -> dict[str, Any]:
    raw = _strip_surrounding_code_fences(str(value or "").strip())
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(raw[start : end + 1])
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


# --- Analysis envelope: markdown parsing ---------------------------------
#
# The AdvancedStrategy analysis pass emits a markdown document with four
# top-level (`## `) sections in this order: ``Segment overview``,
# ``Global context`` (with three ``### `` subsections), ``Examples`` (a fenced
# JSON array of (snippet, record, note) entries), and ``Decision`` (a small
# bullet list of key/value lines). The parser below is intentionally lenient:
# headings are matched case-insensitively, the examples fence is optional, and
# missing fields fall back to safe defaults rather than raising.

_H2_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_H3_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n([\s\S]*?)\n\s*```", re.IGNORECASE)


def _split_markdown_sections(text: str, heading_re: re.Pattern[str]) -> dict[str, str]:
    """Split markdown into sections keyed by case-folded heading text."""
    matches = list(heading_re.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading_key = match.group(1).strip().casefold()
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[heading_key] = text[body_start:body_end].strip()
    return sections


def _find_subsection_body(subsections: dict[str, str], candidates: list[str]) -> str:
    for heading_key, body in subsections.items():
        for candidate in candidates:
            if candidate in heading_key:
                return body.strip()
    return ""


def _parse_examples_section(text: str) -> list[dict[str, Any]]:
    if not text or not text.strip():
        return []
    fence_match = _JSON_FENCE_RE.search(text)
    candidate_text = fence_match.group(1) if fence_match else text
    try:
        parsed = json.loads(candidate_text.strip())
    except Exception:
        # Fall back: maybe the model emitted a bare JSON array without a fence.
        start = candidate_text.find("[")
        end = candidate_text.rfind("]")
        if start == -1 or end <= start:
            return []
        try:
            parsed = json.loads(candidate_text[start : end + 1])
        except Exception:
            return []
    if not isinstance(parsed, list):
        return []
    examples: list[dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        snippet = str(entry.get("snippet") or "").strip()
        record = entry.get("record")
        if not snippet or not isinstance(record, dict):
            continue
        note_value = entry.get("note")
        note_str = str(note_value).strip() if note_value else ""
        examples.append({"snippet": snippet, "record": record, "note": note_str})
        if len(examples) >= MAX_ANALYSIS_EXAMPLES:
            break
    return examples


def _parse_analysis_envelope(raw_text: str) -> AnalysisEnvelope:
    """Parse the AdvancedStrategy analysis pass markdown envelope.

    The envelope has three top-level sections (``## Segment overview``,
    ``## Global context`` with three ``### `` subsections,
    ``## Examples`` with a fenced JSON array).
    Tolerant of malformed output: missing fields fall back to safe defaults.
    If no recognizable headings are present, the raw text is preserved as
    ``global_context.shared_values`` so cross-segment information is not lost.
    """
    text = (raw_text or "").strip()
    if not text:
        return AnalysisEnvelope(
            segment_overview="",
            global_context=_empty_global_context(),
            examples=[],
        )

    sections = _split_markdown_sections(text, _H2_HEADING_RE)
    if not sections:
        # No recognizable structure; keep content alive as shared_values.
        return AnalysisEnvelope(
            segment_overview="",
            global_context={
                **_empty_global_context(),
                "shared_values": text,
            },
            examples=[],
        )

    segment_overview = sections.get("segment overview", "").strip()

    global_block = ""
    for key, body in sections.items():
        if key.startswith("global context"):
            global_block = body
            break
    global_subsections = (
        _split_markdown_sections(global_block, _H3_HEADING_RE) if global_block else {}
    )
    global_context = {
        "shared_values": _find_subsection_body(
            global_subsections, ["shared values", "shared"]
        ),
        "schema_observations": _find_subsection_body(
            global_subsections, ["schema observations", "schema"]
        ),
        "disambiguation_rules": _find_subsection_body(
            global_subsections, ["disambiguation rules", "disambig"]
        ),
    }

    examples = _parse_examples_section(sections.get("examples", ""))

    return AnalysisEnvelope(
        segment_overview=segment_overview,
        global_context=global_context,
        examples=examples,
    )


def _render_global_context_for_extraction(global_context: dict[str, str]) -> str:
    """Render the running global_context dict as a compact extraction prefix."""
    parts: list[str] = []
    shared = (global_context.get("shared_values") or "").strip()
    schema_obs = (global_context.get("schema_observations") or "").strip()
    disambig = (global_context.get("disambiguation_rules") or "").strip()
    if shared:
        parts.append(f"## Shared values\n{shared}")
    if schema_obs:
        parts.append(f"## Schema observations\n{schema_obs}")
    if disambig:
        parts.append(f"## Disambiguation rules\n{disambig}")
    return "\n\n".join(parts).strip()


def _render_examples_for_prompt(examples: list[dict[str, Any]]) -> str:
    """Render the example bank as a markdown string embedded into the system prompt.

    Mirrors the canonical extraction output shape (``{"records": [...]}``) so
    the model sees examples in the same form it should produce. Returns
    ``"(none)"`` when there are no usable examples.
    """
    blocks: list[str] = []
    for index, example in enumerate(examples or [], start=1):
        snippet = str(example.get("snippet") or "").strip()
        record = example.get("record")
        if not snippet or not isinstance(record, dict):
            continue
        record_json = json.dumps({"records": [record]}, ensure_ascii=False, indent=2)
        note = str(example.get("note") or "").strip()
        block_parts = [
            f"Example {index}:",
            "Snippet:",
            snippet,
            "",
            "Expected output:",
            record_json,
        ]
        if note:
            block_parts.extend(["", f"Note: {note}"])
        blocks.append("\n".join(block_parts))
    if not blocks:
        return "(none)"
    return "\n\n".join(blocks)


def _build_forwarded_global_context_message(
    global_context: dict[str, str],
) -> str:
    """Render only the running ``Global context`` as the prior assistant message.

    Per-segment sections (``Segment overview``, ``Examples``, ``Decision``) are
    intentionally omitted from the forwarded state — they are produced fresh
    for each segment.
    """
    return (
        "## Global context\n"
        "\n"
        "### Shared values\n"
        "\n"
        f"{(global_context.get('shared_values') or '').strip()}\n"
        "\n"
        "### Schema observations\n"
        "\n"
        f"{(global_context.get('schema_observations') or '').strip()}\n"
        "\n"
        "### Disambiguation rules\n"
        "\n"
        f"{(global_context.get('disambiguation_rules') or '').strip()}\n"
    )


def _merge_examples_capped(
    running: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    *,
    cap: int = MAX_ANALYSIS_EXAMPLES,
) -> list[dict[str, Any]]:
    """Append new examples to the running bank, deduping by snippet, capped."""
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in (running, incoming):
        for example in source or []:
            snippet = str(example.get("snippet") or "").strip()
            if not snippet:
                continue
            key = snippet.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(example)
            if len(merged) >= cap:
                return merged
    return merged


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _string_richness_score(value: str) -> tuple[int, int]:
    normalized = str(value or "").strip()
    return (
        len(re.sub(r"[^0-9A-Za-z]+", "", normalized)),
        len(normalized),
    )


def _prefer_display_value(existing: str, incoming: str) -> str:
    existing_value = str(existing or "").strip()
    incoming_value = str(incoming or "").strip()
    if not existing_value:
        return incoming_value
    if not incoming_value:
        return existing_value
    return (
        incoming_value
        if _string_richness_score(incoming_value)
        > _string_richness_score(existing_value)
        else existing_value
    )


def _value_signature(value: Any) -> str:
    if isinstance(value, str):
        return f"str:{normalize_record_identifier(value) or value.casefold()}"
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except Exception:  # noqa: BLE001
        return repr(value)


def _merge_values(existing: Any, incoming: Any) -> Any:
    if _is_empty_value(existing):
        return incoming
    if _is_empty_value(incoming):
        return existing
    if _value_signature(existing) == _value_signature(incoming):
        if isinstance(existing, str) and isinstance(incoming, str):
            return _prefer_display_value(existing, incoming)
        return existing

    if isinstance(existing, list):
        merged = list(existing)
        seen = {_value_signature(value) for value in merged}
        for value in incoming if isinstance(incoming, list) else [incoming]:
            signature = _value_signature(value)
            if signature not in seen:
                merged.append(value)
                seen.add(signature)
        return merged

    if isinstance(incoming, list):
        return _merge_values(incoming, existing)

    if isinstance(existing, str) and isinstance(incoming, str):
        preferred = _prefer_display_value(existing, incoming)
        alternate = incoming if preferred == existing else existing
        return [preferred, alternate]

    return [existing, incoming]


def _merge_candidate_records(
    existing: EntityCandidateRecord, incoming: EntityCandidateRecord
) -> EntityCandidateRecord:
    merged_identifier = _prefer_display_value(
        existing.record_identifier, incoming.record_identifier
    )
    merged_column_values = dict(existing.column_values)
    for key, value in incoming.column_values.items():
        if key not in merged_column_values:
            if not _is_empty_value(value):
                merged_column_values[key] = value
            continue
        merged_column_values[key] = _merge_values(merged_column_values.get(key), value)

    return EntityCandidateRecord(
        entity=existing.entity,
        record_identifier=merged_identifier,
        column_values=merged_column_values,
    )


def _coerce_entity_value(value: Any, column_type: EntityColumnType) -> Any:
    if value is None:
        return None

    if column_type == "string":
        text_value = str(value).strip()
        return text_value or None

    if column_type == "date":
        text_value = str(value).strip()
        if not text_value:
            return None
        try:
            normalized = text_value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            return parsed.isoformat()
        except ValueError:
            try:
                parsed = date.fromisoformat(text_value)
                return parsed.isoformat()
            except ValueError:
                return text_value

    if column_type == "number":
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        text_value = str(value).strip().replace(",", "")
        if not text_value:
            return None
        try:
            return int(text_value)
        except ValueError:
            try:
                return float(text_value)
            except ValueError:
                return None

    if column_type == "boolean":
        if isinstance(value, bool):
            return value
        text_value = str(value).strip().casefold()
        if text_value in {"true", "1", "yes", "y"}:
            return True
        if text_value in {"false", "0", "no", "n"}:
            return False
        return None

    return value


def parse_entity_candidates_from_output(
    output: dict[str, Any], entity_definitions: list[EntityDefinition]
) -> list[EntityCandidateRecord]:
    records_value = output.get("records")
    raw_records = records_value if isinstance(records_value, list) else []

    candidates: dict[tuple[str, str], EntityCandidateRecord] = {}

    for entity_definition in entity_definitions:
        entity_name = entity_definition.name

        for raw_record in raw_records:
            if not isinstance(raw_record, dict):
                continue

            column_values: dict[str, Any] = {}
            for column in entity_definition.columns or []:
                coerced_value = _coerce_entity_value(
                    raw_record.get(column.name), column.type
                )
                if coerced_value is not None:
                    column_values[column.name] = coerced_value

            identifier_value = column_values.get(entity_definition.identifier_column)
            if _is_empty_value(identifier_value):
                continue

            record_identifier = str(identifier_value).strip()
            if not record_identifier:
                continue

            dedup_key = (entity_name, normalize_record_identifier(record_identifier))
            candidate = EntityCandidateRecord(
                entity=entity_name,
                record_identifier=record_identifier,
                column_values=column_values,
            )
            if dedup_key in candidates:
                candidates[dedup_key] = _merge_candidate_records(
                    candidates[dedup_key], candidate
                )
            else:
                candidates[dedup_key] = candidate

    return list(candidates.values())


_VERIFICATION_PROMPT = (
    "Are you sure that you have extracted all records for entity '{entity_name}'?. "
    "Can you carefully review source text again and extract missing records. "
    "Return only missing records, do not repeat already listed items."
)


async def _extract_entities_iterative(
    *,
    prompt_template_config: dict[str, Any],
    schema: str,
    entity_definition: EntityDefinition,
    content: str,
    additional_prefix_messages: list[dict[str, str]] | None = None,
    extra_iterations: int = 2,
    inline_analysis: bool = False,
    followup_prompt_template_config: dict[str, Any] | None = None,
    followup_schema: str | None = None,
    extra_template_values: dict[str, str] | None = None,
    cancel_check: Any = None,
) -> tuple[list[EntityCandidateRecord], str]:
    """Run entity extraction with verification iterations.

    Performs an initial extraction pass, then up to ``extra_iterations`` more
    passes where the full conversation history is preserved and the LLM is
    asked to find anything it missed.  Stops early when a verification pass
    returns zero new entities.

    ``additional_prefix_messages`` are prepended to the conversation before
    the segment user message (used by AdvancedStrategy to inject the global
    document analysis as context).

    When ``inline_analysis=True`` (reflective strategy), the first iteration's
    JSON output is expected to include an ``analysis`` field alongside
    ``records``; the analysis is captured and returned. Verification iterations
    use ``followup_prompt_template_config`` / ``followup_schema`` (a records-only
    schema) so the model does not waste tokens repeating the analysis.
    """
    merged: dict[tuple[str, str], EntityCandidateRecord] = {}
    latest_analysis = ""

    # Accumulated conversation history — grows each iteration
    additional_messages: list[dict[str, str]] = list(additional_prefix_messages or [])
    additional_messages.append({"role": "user", "content": content})

    for i in range(1 + max(0, extra_iterations)):
        if cancel_check and await cancel_check():
            break

        if i == 0 or followup_prompt_template_config is None:
            iteration_config = prompt_template_config
            iteration_schema = schema
        else:
            iteration_config = followup_prompt_template_config
            iteration_schema = followup_schema or schema

        template_values: dict[str, str] = {
            "SCHEMA": iteration_schema,
            "ENTITY_NAME": entity_definition.name,
            "EXAMPLES": "(none)",
        }
        if extra_template_values:
            template_values.update(extra_template_values)

        try:
            result = await execute_prompt_template(
                system_name_or_config=iteration_config,
                template_values=template_values,
                template_additional_messages=list(additional_messages),
            )
            raw = _best_effort_json_object_from_text(result.content)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Entity extraction iteration %d failed for entity %s: %s",
                i,
                entity_definition.name,
                exc,
            )
            break

        # Preserve the full assistant response in conversation history
        additional_messages.append({"role": "assistant", "content": result.content})

        if inline_analysis and i == 0:
            analysis_value = str(raw.get("analysis") or "").strip()
            if analysis_value:
                latest_analysis = analysis_value

        # Parse candidates from this iteration and merge
        iteration_candidates = parse_entity_candidates_from_output(
            raw, [entity_definition]
        )
        for candidate in iteration_candidates:
            key = (
                candidate.entity,
                normalize_record_identifier(candidate.record_identifier),
            )
            if key in merged:
                merged[key] = _merge_candidate_records(merged[key], candidate)
            else:
                merged[key] = candidate

        # Early stop: if any pass returned nothing, no point continuing
        if len(iteration_candidates) == 0:
            break

        # Append verification prompt for the next iteration
        if i < extra_iterations:
            verification_msg = _VERIFICATION_PROMPT.replace(
                "{entity_name}", entity_definition.name
            )
            additional_messages.append({"role": "user", "content": verification_msg})

    return list(merged.values()), latest_analysis


def _split_into_segments(
    text_value: str, *, segment_size: int, segment_overlap: float
) -> list[str]:
    text_value = str(text_value or "")
    if not text_value:
        return []

    try:
        seg_size = int(segment_size)
    except Exception:
        seg_size = 18000
    seg_size = max(seg_size, 100)

    try:
        overlap_ratio = float(segment_overlap)
    except Exception:
        overlap_ratio = 0.1
    overlap_ratio = max(0.0, min(overlap_ratio, 0.9))

    if len(text_value) <= seg_size:
        return [text_value]

    overlap_size = int(seg_size * overlap_ratio)
    step_size = max(seg_size - overlap_size, 1)

    segments: list[str] = []
    start = 0
    while start < len(text_value):
        end = min(start + seg_size, len(text_value))
        segments.append(text_value[start:end])
        if end >= len(text_value):
            break
        start += step_size
    return segments


@observe(
    name="Extract entity type from content", channel="production", source="production"
)
async def _extract_entity_from_content(
    *,
    prompt_template_config: dict[str, Any],
    entity_definition: EntityDefinition,
    content: str,
    max_extraction_iterations: int,
    schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
    additional_prefix_messages: list[dict[str, str]] | None = None,
    inline_analysis: bool = False,
    extra_template_values: dict[str, str] | None = None,
    cancel_check: Any = None,
) -> tuple[list[EntityCandidateRecord], str]:
    """Extract all records for a single entity type from a content string.

    Returns ``(candidates, analysis)``. ``analysis`` is the latest analysis text
    when ``inline_analysis=True`` (reflective strategy), otherwise an empty string.
    """

    observability_context.update_current_span(
        input={
            "Entity": entity_definition.name,
            "Max Extraction Iterations": max_extraction_iterations,
            "Schema Format": schema_format,
            "Inline Analysis": inline_analysis,
        }
    )

    def _build_for(*, with_analysis: bool) -> tuple[dict[str, Any], str]:
        if schema_format == "json_schema":
            schema_text = (
                _JSON_SCHEMA_MODE_PROMPT_HINT_REFLECTIVE
                if with_analysis
                else _JSON_SCHEMA_MODE_PROMPT_HINT
            )
            config = dict(prompt_template_config)
            config["response_format"] = build_entity_extraction_response_format(
                entity_definition, include_analysis=with_analysis
            )
            return config, schema_text
        if schema_format == "markdown":
            return (
                prompt_template_config,
                build_entity_extraction_prompt_schema_markdown(
                    [entity_definition], include_analysis=with_analysis
                ),
            )
        return prompt_template_config, build_entity_extraction_prompt_schema_typescript(
            [entity_definition], include_analysis=with_analysis
        )

    config_for_call, entity_schema_text = _build_for(with_analysis=inline_analysis)

    followup_config: dict[str, Any] | None = None
    followup_schema_text: str | None = None
    if inline_analysis and max_extraction_iterations > 1:
        followup_config, followup_schema_text = _build_for(with_analysis=False)

    return await _extract_entities_iterative(
        prompt_template_config=config_for_call,
        schema=entity_schema_text,
        entity_definition=entity_definition,
        content=content,
        additional_prefix_messages=additional_prefix_messages,
        extra_iterations=max_extraction_iterations - 1,
        inline_analysis=inline_analysis,
        followup_prompt_template_config=followup_config,
        followup_schema=followup_schema_text,
        extra_template_values=extra_template_values,
        cancel_check=cancel_check,
    )


# ---------------------------------------------------------------------------
# Extraction strategies
#
# Each strategy decides what (if anything) to do *before* per-segment extraction
# (see ``prepare_context``) and how to inject that into per-segment extraction
# (see ``extract_segment``).  Adding a new mode is: implement a new strategy
# class, add the mode name to ``EXTRACTION_MODES``, and route it in
# ``build_extraction_strategy``.
# ---------------------------------------------------------------------------


class BasicStrategy:
    """Single-prompt per-segment extraction with the verification iteration loop."""

    def __init__(
        self,
        *,
        extraction_prompt_template_config: dict[str, Any],
        schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
    ) -> None:
        self._extraction_config = extraction_prompt_template_config
        self._schema_format: EntityExtractionSchemaFormat = schema_format

    async def prepare_context(
        self,
        *,
        segments: list[str],
        entity_definitions: list[EntityDefinition],
        cancel_check: Any = None,
    ) -> dict[str, Any]:
        return {}

    async def extract_segment(
        self,
        *,
        content: str,
        entity_definition: EntityDefinition,
        context: dict[str, Any],
        max_extraction_iterations: int,
        segment_index: int = 0,
        cancel_check: Any = None,
    ) -> tuple[list[EntityCandidateRecord], dict[str, Any]]:
        del segment_index  # not used by BasicStrategy; accepted for interface parity
        candidates, _ = await _extract_entity_from_content(
            prompt_template_config=self._extraction_config,
            entity_definition=entity_definition,
            content=content,
            max_extraction_iterations=max_extraction_iterations,
            schema_format=self._schema_format,
            cancel_check=cancel_check,
        )
        return candidates, context


_ANALYSIS_LEAD_IN = (
    "The following message is the running global analysis of the source "
    "document, produced by a separate pre-analysis pass. Use it as cross-"
    "segment context when extracting entities from the segment that follows. "
    "Do not extract records directly from the analysis — only from the "
    "segment content."
)

_ANALYSIS_FORWARDED_LEAD_IN = (
    "The following message is the running Global context accumulated from "
    "earlier segments of this document by previous analysis passes. Use it "
    "as cross-segment memory when analyzing the next segment. Note: only the "
    "Global context is forwarded — Examples and per-segment sections were "
    "not carried over and should be produced fresh for the current segment."
)


class AdvancedStrategy:
    """Two-stage strategy: structured analysis envelope, then context-aware extraction.

    The analysis pass walks segments once and emits, for each segment, a markdown
    envelope with three blocks:

    * ``segment_overview`` — chain-of-thought scratchpad. Discarded after the
      call; never fed forward.
    * ``global_context`` — running global state (shared values, schema notes,
      disambiguation rules). Carried forward between analysis calls and used
      as the prefix for every extraction call.
    * ``examples`` — accumulating, capped few-shot bank used to seed
      extraction calls as alternating (snippet, record) message pairs.
    """

    def __init__(
        self,
        *,
        extraction_prompt_template_config: dict[str, Any],
        analysis_prompt_template_config: dict[str, Any],
        schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
    ) -> None:
        self._extraction_config = extraction_prompt_template_config
        self._analysis_config = analysis_prompt_template_config
        self._schema_format: EntityExtractionSchemaFormat = schema_format

    @observe(
        name="Advanced strategy: document analysis pass",
        channel="production",
        source="production",
    )
    async def prepare_context(
        self,
        *,
        segments: list[str],
        entity_definitions: list[EntityDefinition],
        cancel_check: Any = None,
    ) -> dict[str, Any]:
        full_schema = build_entity_schema_summary(entity_definitions)
        entity_names = ", ".join(ed.name for ed in entity_definitions)
        total_segments = len(segments)

        observability_context.update_current_span(
            input={
                "Segments Count": total_segments,
                "Entity Names": entity_names,
            }
        )

        # Analysis output is markdown — no structured-output `response_format`.
        analysis_config = self._analysis_config

        envelopes_built = 0
        running_global_context: dict[str, str] = _empty_global_context()
        running_examples: list[dict[str, Any]] = []

        for index, segment in enumerate(segments):
            if cancel_check and await cancel_check():
                break

            additional_messages: list[dict[str, str]] = []
            if any(running_global_context.values()):
                additional_messages.append(
                    {"role": "user", "content": _ANALYSIS_FORWARDED_LEAD_IN}
                )
                additional_messages.append(
                    {
                        "role": "assistant",
                        "content": _build_forwarded_global_context_message(
                            running_global_context
                        ),
                    }
                )
            additional_messages.append({"role": "user", "content": segment})

            try:
                result = await execute_prompt_template(
                    system_name_or_config=analysis_config,
                    template_values={
                        "SCHEMA": full_schema,
                        "ENTITY_NAMES": entity_names,
                        "SEGMENT_INDEX": str(index + 1),
                        "SEGMENT_COUNT": str(total_segments),
                    },
                    template_additional_messages=additional_messages,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Advanced strategy analysis pass %d/%d failed: %s",
                    index + 1,
                    total_segments,
                    exc,
                )
                continue

            envelope = _parse_analysis_envelope(str(result.content or ""))
            envelopes_built += 1
            running_global_context = envelope.global_context
            running_examples = _merge_examples_capped(
                running_examples, envelope.examples
            )

        observability_context.update_current_span(
            output={
                "Envelopes Built": envelopes_built,
            }
        )

        return {
            "final_global_context": running_global_context,
            "final_examples": running_examples,
        }

    async def extract_segment(
        self,
        *,
        content: str,
        entity_definition: EntityDefinition,
        context: dict[str, Any],
        max_extraction_iterations: int,
        segment_index: int = 0,
        cancel_check: Any = None,
    ) -> tuple[list[EntityCandidateRecord], dict[str, Any]]:
        # Global context and examples are taken from the *final* accumulated
        # state across all segments (built progressively by prepare_context),
        # not from the current segment's envelope. The accumulated state is
        # the most informed view of the document.
        final_global_context: dict[str, str] = (context or {}).get(
            "final_global_context"
        ) or _empty_global_context()
        final_examples: list[dict[str, Any]] = (context or {}).get(
            "final_examples"
        ) or []

        prefix_messages: list[dict[str, str]] = []
        global_text = _render_global_context_for_extraction(final_global_context)
        if global_text:
            prefix_messages.append({"role": "user", "content": _ANALYSIS_LEAD_IN})
            prefix_messages.append({"role": "assistant", "content": global_text})

        examples_text = _render_examples_for_prompt(final_examples)

        candidates, _ = await _extract_entity_from_content(
            prompt_template_config=self._extraction_config,
            entity_definition=entity_definition,
            content=content,
            max_extraction_iterations=max_extraction_iterations,
            schema_format=self._schema_format,
            additional_prefix_messages=prefix_messages,
            extra_template_values={"EXAMPLES": examples_text},
            cancel_check=cancel_check,
        )
        return candidates, context


_REFLECTIVE_LEAD_IN = (
    "The following message is the running analysis for entity '{entity_name}', "
    "built incrementally from earlier segments of this same document. Use it as "
    "cross-segment context, then update it with observations from the next "
    "segment and emit records from that segment."
)


class ReflectiveStrategy:
    """Inline context-aware strategy: per-segment call returns analysis + records.

    Each ``(segment, entity)`` call instructs the model to emit both an updated
    running analysis and the extracted records. The analysis from the previous
    segment for the same entity is fed back into the next call as conversation
    context, so cross-segment knowledge accumulates progressively without a
    separate pre-analysis pass.
    """

    def __init__(
        self,
        *,
        extraction_prompt_template_config: dict[str, Any],
        schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
    ) -> None:
        self._extraction_config = extraction_prompt_template_config
        self._schema_format: EntityExtractionSchemaFormat = schema_format

    async def prepare_context(
        self,
        *,
        segments: list[str],
        entity_definitions: list[EntityDefinition],
        cancel_check: Any = None,
    ) -> dict[str, Any]:
        return {"analyses": {}}

    @observe(
        name="Reflective strategy: segment extraction",
        channel="production",
        source="production",
    )
    async def extract_segment(
        self,
        *,
        content: str,
        entity_definition: EntityDefinition,
        context: dict[str, Any],
        max_extraction_iterations: int,
        segment_index: int = 0,
        cancel_check: Any = None,
    ) -> tuple[list[EntityCandidateRecord], dict[str, Any]]:
        del (
            segment_index
        )  # not used by ReflectiveStrategy; accepted for interface parity
        analyses = dict(((context or {}).get("analyses") or {}))
        prior_analysis = str(analyses.get(entity_definition.name) or "").strip()

        prefix_messages: list[dict[str, str]] = []
        if prior_analysis:
            prefix_messages.append(
                {
                    "role": "user",
                    "content": _REFLECTIVE_LEAD_IN.replace(
                        "{entity_name}", entity_definition.name
                    ),
                }
            )
            prefix_messages.append({"role": "assistant", "content": prior_analysis})

        candidates, new_analysis = await _extract_entity_from_content(
            prompt_template_config=self._extraction_config,
            entity_definition=entity_definition,
            content=content,
            max_extraction_iterations=max_extraction_iterations,
            schema_format=self._schema_format,
            additional_prefix_messages=prefix_messages,
            inline_analysis=True,
            cancel_check=cancel_check,
        )

        if new_analysis:
            analyses[entity_definition.name] = new_analysis
        updated_context = dict(context or {})
        updated_context["analyses"] = analyses
        return candidates, updated_context


async def build_extraction_strategy(
    mode: str,
    *,
    extraction_prompt_template_system_name: str,
    analysis_prompt_template_system_name: str | None,
    schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
) -> BasicStrategy | AdvancedStrategy | ReflectiveStrategy:
    """Resolve prompt configs and return the strategy implementing ``mode``."""
    extraction_config = dict(
        await get_prompt_template_by_system_name_flat(
            extraction_prompt_template_system_name
        )
    )

    if mode == "advanced":
        if not analysis_prompt_template_system_name:
            raise ValueError(
                "analysis_prompt_template_system_name is required for advanced mode"
            )
        analysis_config = dict(
            await get_prompt_template_by_system_name_flat(
                analysis_prompt_template_system_name
            )
        )
        return AdvancedStrategy(
            extraction_prompt_template_config=extraction_config,
            analysis_prompt_template_config=analysis_config,
            schema_format=schema_format,
        )

    if mode == "reflective":
        return ReflectiveStrategy(
            extraction_prompt_template_config=extraction_config,
            schema_format=schema_format,
        )

    if mode != "basic":
        raise ValueError(f"Unknown extraction mode: {mode}")

    return BasicStrategy(
        extraction_prompt_template_config=extraction_config,
        schema_format=schema_format,
    )


@observe(
    name="Extract entities from document", channel="production", source="production"
)
async def _process_document_extraction(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    doc_id: str,
    source_id: str | None,
    content_str: str,
    entity_definitions: list[EntityDefinition],
    strategy: BasicStrategy | AdvancedStrategy | ReflectiveStrategy,
    entity_service: KnowledgeGraphEntityService,
    segment_size: int,
    segment_overlap: float,
    max_extraction_iterations: int,
    cancel_check: Any = None,
) -> dict[str, int]:
    """Extract entities from a single document (document approach).

    Splits content into segments, runs the strategy's pre-analysis (if any),
    extracts each (segment x entity) pair, merges across segments, and upserts
    records.
    """

    upserted_records = 0
    errors = 0
    cancelled = False

    document_candidates: dict[tuple[str, str], EntityCandidateRecord] = {}
    segments = _split_into_segments(
        content_str,
        segment_size=segment_size,
        segment_overlap=segment_overlap,
    )

    observability_context.update_current_span(
        input={
            "Document Id": doc_id,
            "Segments Count": len(segments),
        }
    )

    if not segments:
        return {
            "upserted_records": 0,
            "errors": 0,
            "cancelled": False,
        }

    try:
        strategy_context = await strategy.prepare_context(
            segments=segments,
            entity_definitions=entity_definitions,
            cancel_check=cancel_check,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Strategy pre-analysis failed for document %s: %s", doc_id, exc)
        strategy_context = {}

    if cancel_check and await cancel_check():
        cancelled = True

    for segment_index, segment in enumerate(segments):
        if cancelled:
            break
        for entity_def in entity_definitions:
            if cancel_check and await cancel_check():
                cancelled = True
                break

            try:
                candidates, strategy_context = await strategy.extract_segment(
                    content=segment,
                    entity_definition=entity_def,
                    context=strategy_context,
                    max_extraction_iterations=max_extraction_iterations,
                    segment_index=segment_index,
                    cancel_check=cancel_check,
                )
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning(
                    "Entity extraction failed for document %s entity %s: %s",
                    doc_id,
                    entity_def.name,
                    exc,
                )
                continue

            for candidate in candidates:
                candidate_key = (
                    candidate.entity,
                    normalize_record_identifier(candidate.record_identifier),
                )
                if candidate_key in document_candidates:
                    document_candidates[candidate_key] = _merge_candidate_records(
                        document_candidates[candidate_key],
                        candidate,
                    )
                else:
                    document_candidates[candidate_key] = candidate

    for candidate in document_candidates.values():
        await entity_service.upsert_record(
            db_session,
            graph_id=graph_id,
            entity=candidate.entity,
            record_identifier=candidate.record_identifier,
            column_values=candidate.column_values,
            source_document_id=doc_id,
            source_id=source_id,
        )
        upserted_records += 1

    await db_session.commit()
    return {
        "upserted_records": upserted_records,
        "errors": errors,
        "cancelled": cancelled,
    }


@observe(
    name="Extract entities from document chunks",
    channel="production",
    source="production",
)
async def _process_document_chunks_extraction(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    doc_id: str,
    source_id: str | None,
    chunk_rows: list[Any],
    entity_definitions: list[EntityDefinition],
    strategy: BasicStrategy | AdvancedStrategy | ReflectiveStrategy,
    entity_service: KnowledgeGraphEntityService,
    max_extraction_iterations: int,
    cancel_check: Any = None,
) -> dict[str, int]:
    """Extract entities from chunks belonging to a single document."""

    observability_context.update_current_span(
        input={
            "Document Id": doc_id,
            "Chunk Count": len(chunk_rows),
        }
    )

    processed_chunks = 0
    skipped_chunks = 0
    upserted_records = 0
    errors = 0
    cancelled = False

    chunk_segments: list[tuple[str, str]] = []
    for chunk_row in chunk_rows:
        chunk_id = str(chunk_row.get("id") or "").strip()
        content_str = str(chunk_row.get("content") or "").strip()
        if not chunk_id or not content_str:
            skipped_chunks += 1
            continue
        chunk_segments.append((chunk_id, content_str))

    if not chunk_segments:
        return {
            "processed_chunks": 0,
            "skipped_chunks": skipped_chunks,
            "upserted_records": 0,
            "errors": 0,
            "cancelled": False,
        }

    try:
        strategy_context = await strategy.prepare_context(
            segments=[content for _id, content in chunk_segments],
            entity_definitions=entity_definitions,
            cancel_check=cancel_check,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Strategy pre-analysis failed for document %s chunks: %s", doc_id, exc
        )
        strategy_context = {}

    if cancel_check and await cancel_check():
        return {
            "processed_chunks": 0,
            "skipped_chunks": skipped_chunks,
            "upserted_records": 0,
            "errors": 0,
            "cancelled": True,
        }

    for segment_index, (chunk_id, content_str) in enumerate(chunk_segments):
        if cancel_check and await cancel_check():
            cancelled = True
            break

        processed_chunks += 1

        for entity_def in entity_definitions:
            if cancel_check and await cancel_check():
                cancelled = True
                break

            try:
                chunk_candidates, strategy_context = await strategy.extract_segment(
                    content=content_str,
                    entity_definition=entity_def,
                    context=strategy_context,
                    max_extraction_iterations=max_extraction_iterations,
                    segment_index=segment_index,
                    cancel_check=cancel_check,
                )
            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning(
                    "Entity extraction failed for graph %s doc %s chunk %s entity %s: %s",
                    str(graph_id),
                    doc_id,
                    chunk_id,
                    entity_def.name,
                    exc,
                )
                continue

            for candidate in chunk_candidates:
                await entity_service.upsert_record(
                    db_session,
                    graph_id=graph_id,
                    entity=candidate.entity,
                    record_identifier=candidate.record_identifier,
                    column_values=candidate.column_values,
                    source_document_id=doc_id,
                    source_chunk_id=chunk_id,
                    source_id=source_id,
                )
                upserted_records += 1

        if cancelled:
            break

        await db_session.commit()

    return {
        "processed_chunks": processed_chunks,
        "skipped_chunks": skipped_chunks,
        "upserted_records": upserted_records,
        "errors": errors,
        "cancelled": cancelled,
    }


async def run_graph_llm_entity_extraction(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    approach: EntityExtractionApproach,
    prompt_template_system_name: str,
    entity_definitions: list[EntityDefinition],
    mode: str = DEFAULT_EXTRACTION_MODE,
    analysis_prompt_template_system_name: str | None = None,
    entity_service: KnowledgeGraphEntityService | None = None,
    segment_size: int = 18000,
    segment_overlap: float = 0.1,
    max_extraction_iterations: int = 3,
    schema_format: EntityExtractionSchemaFormat = DEFAULT_SCHEMA_FORMAT,
    progress_callback: Any | None = None,
    cancel_check: Any | None = None,
) -> dict[str, Any]:
    prompt_template_system_name = str(prompt_template_system_name or "").strip()
    if not prompt_template_system_name:
        raise ValueError("prompt_template_system_name is required")

    if approach not in ("document", "chunks"):
        raise ValueError("approach must be 'document' or 'chunks'")

    mode = str(mode or DEFAULT_EXTRACTION_MODE).strip() or DEFAULT_EXTRACTION_MODE
    if mode not in EXTRACTION_MODES:
        raise ValueError(f"Unknown extraction mode: {mode}")

    schema_format_str = str(schema_format or DEFAULT_SCHEMA_FORMAT).strip()
    if schema_format_str not in SCHEMA_FORMATS:
        raise ValueError(f"Unknown schema_format: {schema_format_str}")
    schema_format = schema_format_str  # type: ignore[assignment]

    analysis_prompt_template_system_name = (
        str(analysis_prompt_template_system_name or "").strip() or None
    )

    async def _mark_document_extracted(doc_id: str) -> None:
        """Mark a document's entity_extraction pipeline state as completed."""
        await db_session.execute(
            text(
                f"""
                UPDATE {docs_table_name(graph_id)}
                SET pipeline_state = COALESCE(pipeline_state, '{{}}'::jsonb) || :patch,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "id": doc_id,
                "patch": json.dumps(
                    {
                        "entity_extraction": {
                            "status": "completed",
                            "completed_at": utc_now_isoformat(),
                        }
                    }
                ),
            },
        )
        await db_session.commit()

    if not entity_definitions:
        raise ValueError("entity_definitions is required and cannot be empty")

    logger.info(
        "run_graph_llm_entity_extraction started for graph %s (approach=%s, mode=%s, prompt=%s, analysis_prompt=%s, entity_definitions=%d)",
        graph_id,
        approach,
        mode,
        prompt_template_system_name,
        analysis_prompt_template_system_name,
        len(entity_definitions),
    )

    entity_service = entity_service or KnowledgeGraphEntityService()
    strategy = await build_extraction_strategy(
        mode,
        extraction_prompt_template_system_name=prompt_template_system_name,
        analysis_prompt_template_system_name=analysis_prompt_template_system_name,
        schema_format=schema_format,
    )

    observability_context.update_current_span(
        input={
            "approach": str(approach),
            "mode": mode,
            "entity_definitions_count": len(entity_definitions),
        }
    )

    processed_documents = 0
    processed_chunks = 0
    skipped_documents = 0
    skipped_chunks = 0
    upserted_records = 0
    errors = 0

    docs_tbl = docs_table_name(graph_id)
    chunks_tbl = chunks_table_name(graph_id)

    if approach == "document":
        # Count total documents for progress tracking
        total_docs_res = await db_session.execute(
            text(
                f"""
                SELECT COUNT(*) FROM {docs_tbl}
                WHERE pipeline_state->'entity_extraction'->>'status' IS DISTINCT FROM 'completed'
                """
            )
        )
        total_docs = total_docs_res.scalar_one() or 0
        await db_session.commit()
        logger.info(
            "Entity extraction (document approach): %d documents to process for graph %s",
            total_docs,
            graph_id,
        )
        docs_seen = 0

        if progress_callback:
            await progress_callback(0, total_docs)

        batch_size = 50
        offset = 0
        cancelled = False

        while True:
            if cancel_check and await cancel_check():
                cancelled = True
                break

            batch_res = await db_session.execute(
                text(
                    f"""
                    SELECT
                        id::text AS id,
                        source_id::text AS source_id
                    FROM {docs_tbl}
                    WHERE pipeline_state->'entity_extraction'->>'status' IS DISTINCT FROM 'completed'
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": int(batch_size), "offset": int(offset)},
            )
            batch = batch_res.mappings().all()
            await db_session.commit()

            if not batch:
                break

            for row in batch:
                if cancel_check and await cancel_check():
                    cancelled = True
                    break

                doc_id = str(row.get("id") or "").strip()
                source_id = str(row.get("source_id") or "").strip() or None
                if not doc_id:
                    continue

                content_res = await db_session.execute(
                    text(
                        f"""
                        SELECT
                            NULLIF(content_plaintext, '') AS content
                        FROM {docs_tbl}
                        WHERE id = CAST(:id AS uuid)
                        LIMIT 1
                        """
                    ),
                    {"id": doc_id},
                )
                content = content_res.scalar_one_or_none()
                await db_session.commit()

                content_str = str(content or "").strip()
                if not content_str:
                    skipped_documents += 1
                    docs_seen += 1
                    if progress_callback:
                        await progress_callback(docs_seen, total_docs)
                    continue

                processed_documents += 1
                doc_result = await _process_document_extraction(
                    db_session,
                    graph_id=graph_id,
                    doc_id=doc_id,
                    source_id=source_id,
                    content_str=content_str,
                    entity_definitions=entity_definitions,
                    strategy=strategy,
                    entity_service=entity_service,
                    segment_size=segment_size,
                    segment_overlap=segment_overlap,
                    max_extraction_iterations=max_extraction_iterations,
                    cancel_check=cancel_check,
                )
                upserted_records += doc_result["upserted_records"]
                errors += doc_result["errors"]
                if doc_result.get("cancelled"):
                    cancelled = True
                    break

                if doc_result["errors"] == 0:
                    await _mark_document_extracted(doc_id)

                docs_seen += 1
                logger.debug(
                    "Entity extraction progress for graph %s: %d/%d documents, %d upserted, %d errors",
                    graph_id,
                    docs_seen,
                    total_docs,
                    upserted_records,
                    errors,
                )
                if progress_callback:
                    await progress_callback(docs_seen, total_docs)

            if cancelled:
                break

            offset += len(batch)

        logger.info(
            "run_graph_llm_entity_extraction finished for graph %s: processed=%d, skipped=%d, upserted=%d, errors=%d, cancelled=%s",
            graph_id,
            processed_documents,
            skipped_documents,
            upserted_records,
            errors,
            cancelled,
        )
        return {
            "approach": approach,
            "processed_documents": processed_documents,
            "processed_chunks": processed_chunks,
            "skipped_documents": skipped_documents,
            "skipped_chunks": skipped_chunks,
            "upserted_records": upserted_records,
            "errors": errors,
            "cancelled": cancelled,
        }

    docs_res = await db_session.execute(
        text(
            f"""
            SELECT
                d.id::text AS id,
                d.source_id::text AS source_id
            FROM {docs_tbl} d
            WHERE EXISTS (
                SELECT 1 FROM {chunks_tbl} c WHERE c.document_id = d.id
            )
            AND d.pipeline_state->'entity_extraction'->>'status' IS DISTINCT FROM 'completed'
            ORDER BY d.created_at DESC
            """
        )
    )
    docs_rows = docs_res.mappings().all()
    await db_session.commit()

    total_docs = len(docs_rows)
    logger.info(
        "Entity extraction (chunks approach): %d documents to process for graph %s",
        total_docs,
        graph_id,
    )
    docs_seen = 0

    if progress_callback:
        await progress_callback(0, total_docs)

    cancelled = False

    for drow in docs_rows:
        if cancel_check and await cancel_check():
            cancelled = True
            break

        doc_id = str(drow.get("id") or "").strip()
        source_id = str(drow.get("source_id") or "").strip() or None
        if not doc_id:
            continue

        chunks_res = await db_session.execute(
            text(
                f"""
                SELECT
                    id::text AS id,
                    COALESCE(NULLIF(embedded_content, ''), NULLIF(content, '')) AS content
                FROM {chunks_tbl}
                WHERE document_id = CAST(:doc_id AS uuid)
                ORDER BY index NULLS FIRST, created_at
                """
            ),
            {"doc_id": doc_id},
        )
        chunk_rows = chunks_res.mappings().all()
        await db_session.commit()

        if not chunk_rows:
            skipped_documents += 1
            docs_seen += 1
            if progress_callback:
                await progress_callback(docs_seen, total_docs)
            continue

        chunks_result = await _process_document_chunks_extraction(
            db_session,
            graph_id=graph_id,
            doc_id=doc_id,
            source_id=source_id,
            chunk_rows=list(chunk_rows),
            entity_definitions=entity_definitions,
            strategy=strategy,
            entity_service=entity_service,
            max_extraction_iterations=max_extraction_iterations,
            cancel_check=cancel_check,
        )

        p_chunks = chunks_result["processed_chunks"]
        processed_chunks += p_chunks
        skipped_chunks += chunks_result["skipped_chunks"]
        upserted_records += chunks_result["upserted_records"]
        errors += chunks_result["errors"]
        if chunks_result.get("cancelled"):
            cancelled = True
            break

        if p_chunks > 0:
            processed_documents += 1
        else:
            skipped_documents += 1

        if chunks_result["errors"] == 0:
            await _mark_document_extracted(doc_id)

        docs_seen += 1
        logger.debug(
            "Entity extraction progress for graph %s: %d/%d documents, %d upserted, %d errors",
            graph_id,
            docs_seen,
            total_docs,
            upserted_records,
            errors,
        )
        if progress_callback:
            await progress_callback(docs_seen, total_docs)

    logger.info(
        "run_graph_llm_entity_extraction finished for graph %s: processed=%d, skipped=%d, upserted=%d, errors=%d, cancelled=%s",
        graph_id,
        processed_documents,
        skipped_documents,
        upserted_records,
        errors,
        cancelled,
    )
    return {
        "approach": approach,
        "processed_documents": processed_documents,
        "processed_chunks": processed_chunks,
        "skipped_documents": skipped_documents,
        "skipped_chunks": skipped_chunks,
        "upserted_records": upserted_records,
        "errors": errors,
        "cancelled": cancelled,
    }


async def _update_extraction_status(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
    progress: dict[str, Any] | None = None,
) -> None:
    """Persist entity extraction status into the KG state JSONB column."""
    try:
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = graph_res.scalar_one_or_none()
        if not graph:
            return

        current_state = dict(getattr(graph, "state", None) or {})
        prev_extraction = current_state.get("entity_extraction")
        extraction_status: dict[str, Any] = (
            dict(prev_extraction) if isinstance(prev_extraction, dict) else {}
        )
        # Don't overwrite a cancellation signal with "running"
        current_db_status = extraction_status.get("status")
        if current_db_status == "cancelling" and status == "running":
            pass  # preserve cancellation
        else:
            extraction_status["status"] = status

        if started_at is not None:
            extraction_status["started_at"] = started_at
        if completed_at is not None:
            extraction_status["completed_at"] = completed_at
        if result is not None:
            extraction_status["result"] = result
        if error_message is not None:
            extraction_status["error_message"] = error_message
        if progress is not None:
            extraction_status["progress"] = progress
        elif status in ("completed", "error", "cancelled"):
            extraction_status.pop("progress", None)

        current_state["entity_extraction"] = extraction_status
        graph.state = current_state
        await db_session.commit()
    except Exception:
        logger.warning(
            "Failed to update extraction status for graph %s", graph_id, exc_info=True
        )


async def _is_extraction_cancelled(db_session: AsyncSession, graph_id: UUID) -> bool:
    """Fresh DB read to check if cancellation was requested."""
    try:
        graph_res = await db_session.execute(
            select(KnowledgeGraph.state).where(KnowledgeGraph.id == graph_id)
        )
        state = graph_res.scalar_one_or_none()
        if not state or not isinstance(state, dict):
            return False
        extraction = state.get("entity_extraction")
        return isinstance(extraction, dict) and extraction.get("status") in (
            "cancelling",
            "cancelled",
        )
    except Exception:
        logger.warning(
            "Failed to check cancellation for graph %s", graph_id, exc_info=True
        )
        return False


async def run_entity_extraction(
    db_session: AsyncSession,
    graph_id: UUID,
    data: KnowledgeGraphEntityExtractionRunRequest,
    *,
    entity_service: KnowledgeGraphEntityService | None = None,
) -> dict[str, Any]:
    graph_res = await db_session.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    )
    graph = graph_res.scalar_one_or_none()
    if not graph:
        raise NotFoundException("Graph not found")

    settings = getattr(graph, "settings", None) or {}
    entity_settings = (
        settings.get("entity_extraction") if isinstance(settings, dict) else {}
    ) or {}
    extraction_settings = (
        entity_settings.get("extraction") if isinstance(entity_settings, dict) else {}
    ) or {}

    try:
        entity_definitions = normalize_entity_definitions(
            entity_settings.get("entity_definitions")
            if isinstance(entity_settings, dict)
            else []
        )
    except ValueError as exc:
        raise ClientException(str(exc)) from exc

    approach_raw = (
        str(data.approach).strip()
        if getattr(data, "approach", None) is not None
        else str(extraction_settings.get("approach") or "").strip()
    )
    if approach_raw not in ("chunks", "document"):
        raise ClientException("Extraction approach must be 'chunks' or 'document'")

    mode = (
        str(data.mode).strip()
        if getattr(data, "mode", None) is not None
        else str(extraction_settings.get("mode") or "").strip()
    ) or DEFAULT_EXTRACTION_MODE
    if mode not in EXTRACTION_MODES:
        raise ClientException(
            f"Unknown extraction mode: {mode}. Expected one of {list(EXTRACTION_MODES)}"
        )

    prompt_template_system_name = (
        str(data.prompt_template_system_name).strip()
        if getattr(data, "prompt_template_system_name", None) is not None
        else str(extraction_settings.get("prompt_template_system_name") or "").strip()
    )
    analysis_prompt_template_system_name: str | None = (
        str(data.analysis_prompt_template_system_name).strip()
        if getattr(data, "analysis_prompt_template_system_name", None) is not None
        else str(
            extraction_settings.get("analysis_prompt_template_system_name") or ""
        ).strip()
    ) or None
    reflective_prompt_template_system_name: str | None = (
        str(data.reflective_prompt_template_system_name).strip()
        if getattr(data, "reflective_prompt_template_system_name", None) is not None
        else str(
            extraction_settings.get("reflective_prompt_template_system_name") or ""
        ).strip()
    ) or None

    # Pick the active extraction prompt by mode. Reflective uses its own dedicated
    # template since the prompt itself is structurally different (it must produce
    # analysis + records in one call).
    if mode == "reflective":
        if not reflective_prompt_template_system_name:
            raise ClientException(
                "Reflective prompt template is required for reflective extraction mode"
            )
        active_extraction_prompt = reflective_prompt_template_system_name
    else:
        if not prompt_template_system_name:
            raise ClientException("Prompt template is required to run extraction")
        active_extraction_prompt = prompt_template_system_name

    try:
        await get_prompt_template_by_system_name_flat(active_extraction_prompt)
    except LookupError as exc:
        raise ClientException(
            f"Prompt template '{active_extraction_prompt}' was not found"
        ) from exc

    if mode == "advanced":
        if not analysis_prompt_template_system_name:
            raise ClientException(
                "Analysis prompt template is required for advanced extraction mode"
            )
        try:
            await get_prompt_template_by_system_name_flat(
                analysis_prompt_template_system_name
            )
        except LookupError as exc:
            raise ClientException(
                f"Analysis prompt template '{analysis_prompt_template_system_name}' was not found"
            ) from exc

    segment_size = (
        int(data.segment_size)
        if getattr(data, "segment_size", None) is not None
        else int(extraction_settings.get("segment_size") or 18000)
    )
    segment_overlap = (
        float(data.segment_overlap)
        if getattr(data, "segment_overlap", None) is not None
        else float(extraction_settings.get("segment_overlap") or 0.1)
    )
    max_extraction_iterations = max(
        1,
        int(data.max_extraction_iterations)
        if getattr(data, "max_extraction_iterations", None) is not None
        else int(extraction_settings.get("max_extraction_iterations") or 3),
    )

    schema_format_raw = (
        str(data.schema_format).strip()
        if getattr(data, "schema_format", None) is not None
        else str(extraction_settings.get("schema_format") or "").strip()
    ) or DEFAULT_SCHEMA_FORMAT
    if schema_format_raw not in SCHEMA_FORMATS:
        raise ClientException(
            f"Unknown schema_format: {schema_format_raw}. Expected one of {list(SCHEMA_FORMATS)}"
        )
    schema_format: EntityExtractionSchemaFormat = schema_format_raw  # type: ignore[assignment]

    logger.info(
        "Starting entity extraction for graph %s (approach=%s, mode=%s, prompt=%s, analysis_prompt=%s, segment_size=%d, segment_overlap=%.2f, max_iterations=%d, schema_format=%s)",
        graph_id,
        approach_raw,
        mode,
        active_extraction_prompt,
        analysis_prompt_template_system_name,
        segment_size,
        segment_overlap,
        max_extraction_iterations,
        schema_format,
    )

    entity_svc = entity_service or KnowledgeGraphEntityService()
    await entity_svc.create_table(db_session, graph_id=graph_id)

    await _update_extraction_status(
        db_session, graph_id, status="running", started_at=utc_now_isoformat()
    )

    async def _progress_cb(processed: int, total: int) -> None:
        await _update_extraction_status(
            db_session,
            graph_id,
            status="running",
            progress={"processed": processed, "total": total},
        )

    async def _cancel_check() -> bool:
        return await _is_extraction_cancelled(db_session, graph_id)

    try:
        extraction_result = await run_graph_llm_entity_extraction(
            db_session,
            graph_id=graph_id,
            approach=approach_raw,  # type: ignore[arg-type]
            prompt_template_system_name=active_extraction_prompt,
            entity_definitions=entity_definitions,
            mode=mode,
            analysis_prompt_template_system_name=analysis_prompt_template_system_name,
            entity_service=entity_svc,
            segment_size=segment_size,
            segment_overlap=segment_overlap,
            max_extraction_iterations=max_extraction_iterations,
            schema_format=schema_format,
            progress_callback=_progress_cb,
            cancel_check=_cancel_check,
        )
        final_status = (
            "cancelled" if extraction_result.get("cancelled") else "completed"
        )
        logger.info(
            "Entity extraction %s for graph %s: %s",
            final_status,
            graph_id,
            extraction_result,
        )
        await _update_extraction_status(
            db_session,
            graph_id,
            status=final_status,
            completed_at=utc_now_isoformat(),
            result=extraction_result,
        )
        return extraction_result
    except Exception as exc:
        logger.error(
            "Entity extraction failed for graph %s: %s",
            graph_id,
            exc,
            exc_info=True,
        )
        await _update_extraction_status(
            db_session,
            graph_id,
            status="error",
            completed_at=utc_now_isoformat(),
            error_message=str(exc),
        )
        raise


def is_extraction_task_active(graph_id: UUID) -> bool:
    """Return True if a background extraction task is currently running for this graph."""
    return _active_extraction_tasks.get(graph_id, False)


async def run_entity_extraction_background(
    graph_id: UUID, data_dict: dict[str, Any]
) -> None:
    """Run entity extraction in background with its own database session.

    Called via asyncio.create_task(). Should not raise exceptions to the caller.
    """
    _active_extraction_tasks[graph_id] = True
    try:
        async with alchemy.get_session() as db_session:
            data = KnowledgeGraphEntityExtractionRunRequest(**data_dict)
            await run_entity_extraction(db_session, graph_id, data)
    except Exception:
        logger.error(
            "Background entity extraction failed for graph %s",
            graph_id,
            exc_info=True,
        )
    finally:
        _active_extraction_tasks.pop(graph_id, None)
