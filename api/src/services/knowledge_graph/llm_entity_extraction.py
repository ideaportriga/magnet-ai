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

logger = logging.getLogger(__name__)

EntityExtractionApproach = Literal["document", "chunks"]
EntityColumnType = Literal["string", "number", "boolean", "date"]


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


def build_entity_extraction_prompt_schema(
    entity_definitions: list[EntityDefinition],
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
    lines += ["type ExtractedEntityRecords = {", "  records: {"]
    ts_type_map: dict[EntityColumnType, str] = {
        "string": "string",
        "number": "number",
        "boolean": "boolean",
        "date": "string",
    }

    for entity_definition in entity_definitions:
        lines.append("    /**")
        lines.append(
            f"     * Entity: {entity_definition.name}; Identifier column: {entity_definition.identifier_column}"
        )
        if entity_definition.description:
            for description_line in entity_definition.description.splitlines():
                lines.append(f"     * {description_line}".rstrip())
        lines.append("     */")
        lines.append(f"    {json.dumps(entity_definition.name)}: Array<{{")

        for column in entity_definition.columns or []:
            comment_parts = [f"Type: {column.type}"]
            if column.is_identifier:
                comment_parts.append("Primary identifier")
            if column.description:
                comment_parts.append(column.description)
            lines.append(f"      /** {'; '.join(comment_parts)} */")
            if column.is_required:
                lines.append(
                    f"      {json.dumps(column.name)}: {ts_type_map[column.type]}"
                )
            else:
                lines.append(
                    f"      {json.dumps(column.name)}?: {ts_type_map[column.type]} | null"
                )

        lines.append("")
        lines.append(
            "      /** Detailed reasoning explaining why this record was extracted */"
        )
        lines.append('      "__reasoning": string')
        lines.append("    }>")
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    lines.extend(["  }", "}"])
    return "\n".join(lines).strip() + "\n"


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
        if key == "__reasoning":
            continue
        if key not in merged_column_values:
            if not _is_empty_value(value):
                merged_column_values[key] = value
            continue
        merged_column_values[key] = _merge_values(merged_column_values.get(key), value)

    existing_reasoning = str(existing.column_values.get("__reasoning") or "").strip()
    incoming_reasoning = str(incoming.column_values.get("__reasoning") or "").strip()
    if existing_reasoning and incoming_reasoning:
        if incoming_reasoning != existing_reasoning:
            merged_column_values["__reasoning"] = (
                f"{existing_reasoning} | {incoming_reasoning}"
            )
    elif incoming_reasoning:
        merged_column_values["__reasoning"] = incoming_reasoning

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
    records_by_entity = records_value if isinstance(records_value, dict) else {}
    entity_map = {entity.name: entity for entity in entity_definitions}

    candidates: dict[tuple[str, str], EntityCandidateRecord] = {}

    for entity_name, entity_definition in entity_map.items():
        raw_records = records_by_entity.get(entity_name)
        if not isinstance(raw_records, list):
            continue

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

            reasoning = raw_record.get("__reasoning")
            if isinstance(reasoning, str) and reasoning.strip():
                column_values["__reasoning"] = reasoning.strip()

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


async def _extract_entities_from_content(
    *,
    prompt_template_config: dict[str, Any],
    schema: str,
    entity_definition: EntityDefinition,
    content: str,
) -> dict[str, Any]:
    result = await execute_prompt_template(
        system_name_or_config=prompt_template_config,
        template_values={"SCHEMA": schema, "ENTITY_NAME": entity_definition.name},
        template_additional_messages=[{"role": "user", "content": content}],
    )
    return _best_effort_json_object_from_text(result.content)


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
    name="Knowledge graph entity extraction",
    channel="production",
    source="production",
    capture_input=False,
    capture_output=False,
)
async def run_graph_llm_entity_extraction(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    approach: EntityExtractionApproach,
    prompt_template_system_name: str,
    entity_definitions: list[EntityDefinition],
    entity_service: KnowledgeGraphEntityService | None = None,
    segment_size: int = 18000,
    segment_overlap: float = 0.1,
) -> dict[str, Any]:
    prompt_template_system_name = str(prompt_template_system_name or "").strip()
    if not prompt_template_system_name:
        raise ValueError("prompt_template_system_name is required")

    if approach not in ("document", "chunks"):
        raise ValueError("approach must be 'document' or 'chunks'")

    if not entity_definitions:
        raise ValueError("entity_definitions is required and cannot be empty")

    entity_service = entity_service or KnowledgeGraphEntityService()
    prompt_template_config = dict(
        await get_prompt_template_by_system_name_flat(prompt_template_system_name)
    )

    try:
        observability_context.update_current_span(
            extra_data={
                "graph_id": str(graph_id),
                "approach": str(approach),
                "prompt_template_system_name": prompt_template_system_name,
                "segment_size": int(segment_size),
                "segment_overlap": float(segment_overlap),
                "entity_definitions_count": len(entity_definitions),
            }
        )
    except Exception:
        pass

    processed_documents = 0
    processed_chunks = 0
    skipped_documents = 0
    skipped_chunks = 0
    upserted_records = 0
    errors = 0

    docs_tbl = docs_table_name(graph_id)
    chunks_tbl = chunks_table_name(graph_id)

    if approach == "document":
        batch_size = 50
        offset = 0

        while True:
            batch_res = await db_session.execute(
                text(
                    f"""
                    SELECT
                        id::text AS id,
                        source_id::text AS source_id
                    FROM {docs_tbl}
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
                    continue

                processed_documents += 1
                document_candidates: dict[tuple[str, str], EntityCandidateRecord] = {}
                segments = _split_into_segments(
                    content_str,
                    segment_size=segment_size,
                    segment_overlap=segment_overlap,
                )

                for segment in segments:
                    for entity_def in entity_definitions:
                        entity_schema = build_entity_extraction_prompt_schema(
                            [entity_def]
                        )
                        try:
                            extracted = await _extract_entities_from_content(
                                prompt_template_config=prompt_template_config,
                                schema=entity_schema,
                                entity_definition=entity_def,
                                content=segment,
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

                        for candidate in parse_entity_candidates_from_output(
                            extracted, [entity_def]
                        ):
                            candidate_key = (
                                candidate.entity,
                                normalize_record_identifier(
                                    candidate.record_identifier
                                ),
                            )
                            if candidate_key in document_candidates:
                                document_candidates[candidate_key] = (
                                    _merge_candidate_records(
                                        document_candidates[candidate_key],
                                        candidate,
                                    )
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

            offset += len(batch)

        return {
            "approach": approach,
            "processed_documents": processed_documents,
            "processed_chunks": processed_chunks,
            "skipped_documents": skipped_documents,
            "skipped_chunks": skipped_chunks,
            "upserted_records": upserted_records,
            "errors": errors,
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
            ORDER BY d.created_at DESC
            """
        )
    )
    docs_rows = docs_res.mappings().all()
    await db_session.commit()

    for drow in docs_rows:
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
            continue

        had_any_chunk_content = False

        for chunk_row in chunk_rows:
            chunk_id = str(chunk_row.get("id") or "").strip()
            content_str = str(chunk_row.get("content") or "").strip()
            if not chunk_id or not content_str:
                skipped_chunks += 1
                continue

            had_any_chunk_content = True
            processed_chunks += 1

            for entity_def in entity_definitions:
                entity_schema = build_entity_extraction_prompt_schema([entity_def])
                try:
                    extracted = await _extract_entities_from_content(
                        prompt_template_config=prompt_template_config,
                        schema=entity_schema,
                        entity_definition=entity_def,
                        content=content_str,
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

                chunk_candidates = parse_entity_candidates_from_output(
                    extracted, [entity_def]
                )
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

            await db_session.commit()

        if had_any_chunk_content:
            processed_documents += 1
        else:
            skipped_documents += 1

    return {
        "approach": approach,
        "processed_documents": processed_documents,
        "processed_chunks": processed_chunks,
        "skipped_documents": skipped_documents,
        "skipped_chunks": skipped_chunks,
        "upserted_records": upserted_records,
        "errors": errors,
    }


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

    prompt_template_system_name = (
        str(data.prompt_template_system_name).strip()
        if getattr(data, "prompt_template_system_name", None) is not None
        else str(extraction_settings.get("prompt_template_system_name") or "").strip()
    )
    if not prompt_template_system_name:
        raise ClientException("Prompt template is required to run extraction")

    try:
        await get_prompt_template_by_system_name_flat(prompt_template_system_name)
    except LookupError as exc:
        raise ClientException(
            f"Prompt template '{prompt_template_system_name}' was not found"
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

    entity_svc = entity_service or KnowledgeGraphEntityService()
    await entity_svc.create_table(db_session, graph_id=graph_id)

    return await run_graph_llm_entity_extraction(
        db_session,
        graph_id=graph_id,
        approach=approach_raw,  # type: ignore[arg-type]
        prompt_template_system_name=prompt_template_system_name,
        entity_definitions=entity_definitions,
        entity_service=entity_svc,
        segment_size=segment_size,
        segment_overlap=segment_overlap,
    )
