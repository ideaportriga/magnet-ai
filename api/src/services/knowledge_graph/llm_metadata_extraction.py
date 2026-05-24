from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, Literal
from uuid import UUID

import yaml
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    chunks_table_name,
    docs_table_name,
)
from services.knowledge_graph.metadata_services import (
    accumulate_extracted_metadata_fields,
)
from services.knowledge_graph.models import MetadataMultiValueContainer
from services.knowledge_graph.readers import ChunkDocumentReader
from services.knowledge_graph.utils import normalize_metadata_value
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from utils.datetime_utils import utc_now_isoformat

# Emit an INFO-level heartbeat log every N documents during extraction loops.
_METADATA_HEARTBEAT_INTERVAL = 10

logger = logging.getLogger(__name__)

# Registry of actively running metadata extraction tasks keyed by graph_id.
# Holds the Task object itself (not a bool) so the event loop keeps a strong
# reference and cannot garbage-collect / silently cancel the task mid-run.
_active_metadata_tasks: dict[UUID, asyncio.Task[Any]] = {}

MetadataExtractionApproach = Literal["document", "chunks"]


def is_metadata_extraction_task_active(graph_id: UUID) -> bool:
    """Return True if a background metadata extraction task is running for this graph."""
    task = _active_metadata_tasks.get(graph_id)
    return task is not None and not task.done()


async def reconcile_stale_metadata_extractions() -> int:
    """Mark orphan 'running'/'cancelling' metadata extractions as 'interrupted'.

    Called once at process startup. Any graph whose state.metadata_extraction.status
    is 'running' or 'cancelling' must be stale — no in-process task can possibly
    own it because the process just started. Also updates per-document
    pipeline_state.metadata_extraction.status so pipeline-strip stats reflect the
    interrupted state. Returns the number of graph rows updated.
    """
    updated = 0
    affected_graph_ids: list[UUID] = []
    try:
        async with alchemy.get_session() as db_session:
            res = await db_session.execute(select(KnowledgeGraph))
            graphs = res.scalars().all()
            for graph in graphs:
                state = getattr(graph, "state", None)
                if not isinstance(state, dict):
                    continue
                extraction = state.get("metadata_extraction")
                if not isinstance(extraction, dict):
                    continue
                status = extraction.get("status")
                if status not in ("running", "cancelling"):
                    continue
                new_state = dict(state)
                new_extraction = dict(extraction)
                new_extraction["status"] = "interrupted"
                new_extraction["completed_at"] = utc_now_isoformat()
                new_extraction["error_message"] = (
                    "Process restarted while extraction was running"
                )
                new_state["metadata_extraction"] = new_extraction
                graph.state = new_state
                affected_graph_ids.append(graph.id)
                updated += 1
            if updated:
                await db_session.commit()
                logger.warning(
                    "Reconciled %d stale metadata_extraction row(s) to 'interrupted'",
                    updated,
                )
    except Exception:
        logger.error(
            "Failed to reconcile stale metadata extractions on startup",
            exc_info=True,
        )
        return updated

    # Best-effort: mark per-document metadata_extraction states as 'interrupted'
    # so pipeline-strip stats no longer show stale metadata_running counts.
    _reconcile_error_msg = "Process restarted while extraction was running"
    _now = utc_now_isoformat()
    for graph_id in affected_graph_ids:
        try:
            async with alchemy.get_session() as doc_session:
                await doc_session.execute(
                    text(
                        f"""
                        UPDATE {docs_table_name(graph_id)}
                        SET pipeline_state = COALESCE(pipeline_state, '{{}}'::jsonb) ||
                            jsonb_build_object('metadata_extraction',
                                COALESCE(pipeline_state->'metadata_extraction', '{{}}'::jsonb) ||
                                jsonb_build_object(
                                    'status', 'interrupted',
                                    'completed_at', CAST(:completed_at AS text),
                                    'error_message', CAST(:error_message AS text)
                                )
                            ),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE pipeline_state->'metadata_extraction'->>'status' = 'running'
                        """  # noqa: S608
                    ),
                    {"completed_at": _now, "error_message": _reconcile_error_msg},
                )
                await doc_session.commit()
        except Exception:
            logger.warning(
                "Failed to reconcile document metadata_extraction states for graph %s on startup",
                graph_id,
                exc_info=True,
            )

    return updated


async def update_graph_metadata_extraction_status(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    status: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    result: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> None:
    """Persist metadata extraction status into the KG state JSONB column."""
    try:
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = graph_res.scalar_one_or_none()
        if not graph:
            return

        current_state = dict(getattr(graph, "state", None) or {})
        prev = current_state.get("metadata_extraction")
        extraction_status: dict[str, Any] = dict(prev) if isinstance(prev, dict) else {}
        extraction_status["status"] = status

        if started_at is not None:
            extraction_status["started_at"] = started_at
        if completed_at is not None:
            extraction_status["completed_at"] = completed_at
        if result is not None:
            extraction_status["result"] = result
        if error_message is not None:
            extraction_status["error_message"] = error_message

        current_state["metadata_extraction"] = extraction_status
        graph.state = current_state
        await db_session.commit()
    except Exception:
        logger.warning(
            "Failed to update metadata extraction status for graph %s",
            graph_id,
            exc_info=True,
        )


async def mark_metadata_extraction_interrupted(graph_id: UUID, reason: str) -> None:
    """Write 'interrupted' status to DB using a fresh session.

    Used when the task was cancelled (GC, shutdown, SIGTERM) and the original
    session may be unusable. Best-effort: failures are logged but not raised.
    """
    try:
        async with alchemy.get_session() as cleanup_session:
            await update_graph_metadata_extraction_status(
                cleanup_session,
                graph_id,
                status="interrupted",
                completed_at=utc_now_isoformat(),
                error_message=reason,
            )
    except Exception:
        logger.error(
            "Failed to mark interrupted metadata extraction for graph %s",
            graph_id,
            exc_info=True,
        )


def log_metadata_extraction_outcome(graph_id: UUID):
    """Return a Task done-callback that logs the final outcome."""

    def _cb(task: asyncio.Task[Any]) -> None:
        _active_metadata_tasks.pop(graph_id, None)
        try:
            if task.cancelled():
                logger.error(
                    "Metadata extraction task CANCELLED for graph %s (likely GC, "
                    "shutdown, or external cancel)",
                    graph_id,
                )
                return
            exc = task.exception()
            if exc is not None:
                logger.error(
                    "Metadata extraction task FAILED for graph %s",
                    graph_id,
                    exc_info=exc,
                )
            else:
                logger.info(
                    "Metadata extraction task finished cleanly for graph %s",
                    graph_id,
                )
        except asyncio.CancelledError:
            logger.error(
                "Metadata extraction task CANCELLED for graph %s (during outcome check)",
                graph_id,
            )
        except Exception:
            logger.error(
                "Error inspecting metadata extraction task outcome for graph %s",
                graph_id,
                exc_info=True,
            )

    return _cb


async def run_metadata_extraction_background(
    graph_id: UUID, data_dict: dict[str, Any]
) -> None:
    """Run metadata extraction in background with its own database session.

    Called via asyncio.create_task(). Should not raise exceptions to the caller.
    """
    # Local imports to avoid circular dependencies at module load time.
    from core.domain.knowledge_graph.schemas import (
        KnowledgeGraphMetadataExtractionRunRequest,
    )
    from core.domain.knowledge_graph.services.knowledge_graph_metadata_service import (
        KnowledgeGraphMetadataService,
    )

    try:
        async with alchemy.get_session() as db_session:
            data = KnowledgeGraphMetadataExtractionRunRequest(**data_dict)
            service = KnowledgeGraphMetadataService()
            result = await service.run_metadata_extraction(db_session, graph_id, data)
            await update_graph_metadata_extraction_status(
                db_session,
                graph_id,
                status="completed",
                completed_at=utc_now_isoformat(),
                result=result.model_dump() if hasattr(result, "model_dump") else None,
            )
    except asyncio.CancelledError:
        logger.warning(
            "Background metadata extraction cancelled for graph %s — "
            "marking as interrupted",
            graph_id,
        )
        await mark_metadata_extraction_interrupted(
            graph_id, reason="Task was cancelled (shutdown, GC, or restart)"
        )
        raise
    except Exception as exc:
        logger.error(
            "Background metadata extraction failed for graph %s",
            graph_id,
            exc_info=True,
        )
        try:
            async with alchemy.get_session() as cleanup_session:
                await update_graph_metadata_extraction_status(
                    cleanup_session,
                    graph_id,
                    status="error",
                    completed_at=utc_now_isoformat(),
                    error_message=str(exc),
                )
        except Exception:
            logger.error(
                "Failed to record error status for metadata extraction graph %s",
                graph_id,
                exc_info=True,
            )


def build_typescript_schema_from_field_definitions(field_definitions: Any) -> str:
    """Build a TypeScript interface schema string from KG metadata field_definitions.

    Intended for prompt templates as {SCHEMA}.
    """

    def _is_valid_ts_identifier(name: str) -> bool:
        return bool(re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", name))

    def _ts_prop_name(name: str) -> str:
        # Quote names that aren't valid TS identifiers.
        if _is_valid_ts_identifier(name):
            return name
        return json.dumps(name, ensure_ascii=False)

    defs = field_definitions if isinstance(field_definitions, list) else []

    lines: list[str] = ["interface ExtractedMetadata {"]

    for fd in defs:
        if not isinstance(fd, dict):
            continue

        name = str(fd.get("name") or "").strip()
        if not name:
            continue

        display_name = str(fd.get("display_name") or "").strip()
        description = str(fd.get("description") or "").strip()
        llm_hint = str(fd.get("llm_extraction_hint") or "").strip()

        value_type = str(fd.get("value_type") or "").strip().lower()
        is_multiple = bool(fd.get("is_multiple"))

        allowed_values_raw = fd.get("allowed_values")
        allowed_values: list[tuple[str, str | None]] = []
        if isinstance(allowed_values_raw, list):
            seen: set[str] = set()
            for av in allowed_values_raw:
                if not isinstance(av, dict):
                    continue
                val = str(av.get("value") or "").strip()
                if not val or val in seen:
                    continue
                seen.add(val)
                hint = str(av.get("hint") or "").strip() or None
                allowed_values.append((val, hint))

        # Map value types to TS types.
        # Note: value_type="array" in our models means "array-ish"; we treat it as element type `any`.
        scalar_ts_type: str
        if allowed_values:
            scalar_ts_type = " | ".join(
                json.dumps(v, ensure_ascii=False) for v, _ in allowed_values
            )
        else:
            match value_type:
                case "string":
                    scalar_ts_type = "string"
                case "number":
                    scalar_ts_type = "number"
                case "boolean":
                    scalar_ts_type = "boolean"
                case "date":
                    # ISO date string (YYYY-MM-DD or full ISO 8601)
                    scalar_ts_type = "string"
                case "object":
                    scalar_ts_type = "Record<string, any>"
                case "array":
                    scalar_ts_type = "any"
                case _:
                    scalar_ts_type = "any"

        is_array = is_multiple or value_type == "array"
        if is_array:
            element = scalar_ts_type
            if "|" in element:
                element = f"({element})"
            ts_type = f"{element}[]"
        else:
            ts_type = scalar_ts_type

        comment_lines: list[str] = []
        if display_name and display_name != name:
            comment_lines.append(f"Display: {display_name}")
        if description:
            comment_lines.append(description)
        comment_lines.append(
            f"Value type: {value_type or 'unknown'}; Multiple: {bool(is_array)}"
        )
        if allowed_values:
            comment_lines.append("Allowed values:")
            for v, hint in allowed_values:
                comment_lines.append(f"- {v}{f' ({hint})' if hint else ''}")
        if llm_hint:
            comment_lines.append("LLM extraction hint:")
            comment_lines.extend(llm_hint.splitlines())

        if comment_lines:
            lines.append("  /**")
            for cl in comment_lines:
                for cl_line in str(cl).splitlines():
                    lines.append(f"   * {cl_line}".rstrip())
            lines.append("   */")

        is_required = bool(fd.get("is_required"))
        if is_required:
            lines.append(f"  {_ts_prop_name(name)}: {ts_type};")
        else:
            lines.append(f"  {_ts_prop_name(name)}?: {ts_type} | null;")
        lines.append("")

    # Trim trailing blank line if present
    if lines and lines[-1] == "":
        lines.pop()

    lines.append("}")
    return "\n".join(lines).strip() + "\n"


def _strip_surrounding_code_fences(value: str) -> str:
    if not value:
        return value
    match = re.match(r"^\s*```[^\n]*\n([\s\S]*?)\n?\s*```\s*$", value, flags=re.DOTALL)
    return match.group(1).strip() if match else value.strip()


def _best_effort_json_object_from_text(value: str) -> dict[str, Any]:
    """Parse a JSON/YAML object from LLM output (best-effort).

    Prompt templates may return either:
    - JSON object, or
    - YAML mapping (commonly used for human-readable extraction output).

    Models sometimes wrap output in code fences or add extra commentary. We attempt to:
    - strip code fences
    - parse as JSON
    - parse as YAML
    - otherwise parse the substring between the first '{' and the last '}'
    """
    raw = _strip_surrounding_code_fences(str(value or "").strip())
    if not raw:
        return {}

    # Fast-path: exact JSON object
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    # YAML mapping (JSON is a subset of YAML, but we keep JSON as the preferred fast-path)
    try:
        parsed_yaml = yaml.safe_load(raw)
        return parsed_yaml if isinstance(parsed_yaml, dict) else {}
    except yaml.YAMLError:
        pass

    # Best-effort: find first {...} region
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Last-chance: YAML parse of extracted {...} region
    try:
        parsed_yaml = yaml.safe_load(raw[start : end + 1])
        return parsed_yaml if isinstance(parsed_yaml, dict) else {}
    except yaml.YAMLError:
        return {}


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _append_discovery_value(
    bucket: dict[str, list[Any]], *, key: str, value: Any
) -> None:
    """Accumulate per-field values for discovered-metadata counting (keeps duplicates)."""
    if _is_empty_value(value):
        return
    if isinstance(value, (list, tuple, set)):
        for v in value:
            _append_discovery_value(bucket, key=key, value=v)
        return
    bucket.setdefault(key, []).append(value)


def _merge_storage_value(storage: dict[str, Any], *, key: str, value: Any) -> None:
    """Merge a value into a JSON-friendly dict for persistence (keeps unique values)."""
    if _is_empty_value(value):
        return

    # Flatten simple lists into repeated merges for stable storage
    if isinstance(value, (list, tuple, set)):
        for v in value:
            _merge_storage_value(storage, key=key, value=v)
        return

    if key not in storage or _is_empty_value(storage.get(key)):
        storage[key] = value
        return

    existing = storage.get(key)
    if existing == value:
        return

    if isinstance(existing, list):
        if value not in existing:
            existing.append(value)
        storage[key] = existing
        return

    # Promote scalar -> list
    storage[key] = [existing, value] if value != existing else existing


def _build_discovery_metadata(values: dict[str, list[Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, vs in (values or {}).items():
        if not k or not isinstance(k, str):
            continue
        cleaned = [v for v in (vs or []) if not _is_empty_value(v)]
        if not cleaned:
            continue
        if len(cleaned) == 1:
            out[k] = cleaned[0]
        else:
            out[k] = MetadataMultiValueContainer.from_iterable(cleaned)
    return out


@observe(
    name="Knowledge graph entity extraction (LLM)",
    channel="production",
    source="production",
    capture_input=False,
    capture_output=False,
)
async def _extract_metadata_from_content(
    *,
    prompt_template_system_name: str,
    schema: str | None = None,
    content: str,
) -> dict[str, Any]:
    # Avoid capturing potentially large/sensitive content in spans; record only sizes/ids.
    schema_str = str(schema or "")
    try:
        observability_context.update_current_span(
            extra_data={
                "prompt_template_system_name": str(prompt_template_system_name or ""),
                "content_chars": len(str(content or "")),
                "schema_chars": len(schema_str),
                "expected_format": "yaml_or_json",
            }
        )
    except Exception:
        pass

    user_content = (
        "Extract metadata from the following content.\n"
        "Return ONLY a YAML mapping (no extra commentary).\n\n"
        f"```text\n{content}\n```"
    )
    result = await execute_prompt_template(
        system_name_or_config=prompt_template_system_name,
        template_values={"SCHEMA": schema_str},
        template_additional_messages=[{"role": "user", "content": user_content}],
    )
    return _best_effort_json_object_from_text(result.content)


async def _write_metadata_extraction_state(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    document_id: str,
    state: dict[str, Any],
) -> None:
    """Merge a metadata_extraction patch into a document's pipeline_state JSONB.

    Mirrors the entity-extraction pattern (`_mark_document_extracted`) so the
    document table carries a uniform per-phase status that the frontend can
    read.
    """
    docs_tbl = docs_table_name(graph_id)
    try:
        await db_session.execute(
            text(
                f"""
                UPDATE {docs_tbl}
                SET pipeline_state = COALESCE(pipeline_state, '{{}}'::jsonb) || :patch,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "id": document_id,
                "patch": json.dumps({"metadata_extraction": state}),
            },
        )
        await db_session.commit()
    except Exception as exc:  # noqa: BLE001
        # Best-effort: never let pipeline state writes mask the real extraction.
        logger.warning(
            "Failed to write metadata_extraction state for document %s: %s",
            document_id,
            exc,
        )


async def _upsert_document_llm_metadata(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    document_id: str,
    llm_metadata: dict[str, Any],
) -> None:
    """Persist LLM metadata into the per-graph documents table under metadata.llm."""
    if not llm_metadata:
        return

    docs_tbl = docs_table_name(graph_id)
    try:
        normalized_metadata = normalize_metadata_value({"llm": llm_metadata})
        metadata_json = json.dumps(normalized_metadata, ensure_ascii=False, default=str)
    except Exception:  # noqa: BLE001
        logger.warning("Failed to serialize LLM metadata for document %s", document_id)
        return

    await db_session.execute(
        text(
            f"""
            UPDATE {docs_tbl}
            SET metadata = COALESCE(metadata, '{{}}'::jsonb) || CAST(:metadata_json AS jsonb),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {"id": document_id, "metadata_json": metadata_json},
    )


@observe(
    name="Knowledge graph metadata extraction",
    channel="production",
    source="production",
    capture_input=False,
    capture_output=False,
)
async def run_graph_llm_metadata_extraction(
    db_session: AsyncSession,
    *,
    graph_id: UUID,
    approach: MetadataExtractionApproach,
    prompt_template_system_name: str,
    extraction_field_settings: dict[str, dict[str, Any]],
    schema: str | None = None,
    segment_size: int = 18000,
    segment_overlap: float = 0.1,
    document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run LLM metadata extraction for all items in a knowledge graph.

    - document: runs extraction on full document text (with optional segmentation)
    - chunks: runs extraction on chunks and merges results per document
    """
    prompt_template_system_name = str(prompt_template_system_name or "").strip()
    if not prompt_template_system_name:
        raise ValueError("prompt_template_system_name is required")

    if approach not in ("document", "chunks"):
        raise ValueError("approach must be 'document' or 'chunks'")

    if not isinstance(extraction_field_settings, dict) or not extraction_field_settings:
        raise ValueError("extraction_field_settings is required and cannot be empty")

    try:
        observability_context.update_current_span(
            extra_data={
                "graph_id": str(graph_id),
                "approach": str(approach),
                "prompt_template_system_name": prompt_template_system_name,
                "schema_chars": len(str(schema or "")),
                "segment_size": int(segment_size),
                "segment_overlap": float(segment_overlap),
                "extraction_fields_count": len(extraction_field_settings),
            }
        )
    except Exception:
        pass

    processed_documents = 0
    processed_chunks = 0
    skipped_documents = 0
    skipped_chunks = 0
    errors = 0

    docs_tbl = docs_table_name(graph_id)
    chunks_tbl = chunks_table_name(graph_id)

    if approach == "document":
        # NOTE: Do NOT use server-side cursor streaming here. We intentionally process
        # documents in batches and commit per document to avoid keeping a DB transaction
        # open while calling the LLM (which can take a long time).
        batch_size = 50
        offset = 0
        loop_start = time.monotonic()
        docs_seen = 0

        while True:
            doc_id_filter = (
                "AND d.id = ANY(CAST(:document_ids AS uuid[]))"
                if document_ids is not None
                else ""
            )
            batch_res = await db_session.execute(
                text(
                    f"""
                    SELECT
                        id::text AS id
                    FROM {docs_tbl} d
                    WHERE EXISTS (
                        SELECT 1 FROM {chunks_tbl} c WHERE c.document_id = d.id
                    )
                    {doc_id_filter}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {
                    "limit": int(batch_size),
                    "offset": int(offset),
                    **(
                        {"document_ids": document_ids}
                        if document_ids is not None
                        else {}
                    ),
                },
            )
            batch = batch_res.mappings().all()
            # End the read transaction before any LLM calls
            await db_session.commit()

            if not batch:
                break

            for row in batch:
                doc_id = str(row.get("id") or "").strip()
                if not doc_id:
                    continue

                # Reconstruct content from chunks and segment it (short read transaction)
                chunk_reader = await ChunkDocumentReader.load(
                    db_session,
                    graph_id=graph_id,
                    document_id=doc_id,
                )
                segments = chunk_reader.as_segments(
                    segment_size=segment_size,
                    segment_overlap=segment_overlap,
                )
                await db_session.commit()  # close transaction before LLM calls

                if not segments:
                    skipped_documents += 1
                    continue

                processed_documents += 1

                doc_started_at = utc_now_isoformat()
                await _write_metadata_extraction_state(
                    db_session,
                    graph_id=graph_id,
                    document_id=doc_id,
                    state={"status": "running", "started_at": doc_started_at},
                )

                storage: dict[str, Any] = {}
                discovery_values: dict[str, list[Any]] = {}
                segment_errors = 0
                last_segment_error: str | None = None

                for segment in segments:
                    try:
                        extracted = await _extract_metadata_from_content(
                            prompt_template_system_name=prompt_template_system_name,
                            schema=schema,
                            content=segment,
                        )
                    except Exception as exc:  # noqa: BLE001
                        errors += 1
                        segment_errors += 1
                        last_segment_error = str(exc)
                        logger.warning(
                            "Metadata extraction failed for document %s: %s",
                            doc_id,
                            exc,
                        )
                        continue

                    if not extracted:
                        continue

                    for raw_k, v in extracted.items():
                        k = str(raw_k or "").strip()
                        if not k:
                            continue
                        _append_discovery_value(discovery_values, key=k, value=v)
                        _merge_storage_value(storage, key=k, value=v)

                # Persist + update discovered fields (best-effort)
                if storage:
                    await _upsert_document_llm_metadata(
                        db_session,
                        graph_id=graph_id,
                        document_id=doc_id,
                        llm_metadata=storage,
                    )

                discovery_metadata = _build_discovery_metadata(discovery_values)
                if discovery_metadata:
                    await accumulate_extracted_metadata_fields(
                        db_session,
                        graph_id=graph_id,
                        metadata=discovery_metadata,
                        extraction_field_settings=extraction_field_settings,
                    )

                await db_session.commit()

                # Reflect the final per-document outcome on pipeline_state.
                if segment_errors and not storage:
                    await _write_metadata_extraction_state(
                        db_session,
                        graph_id=graph_id,
                        document_id=doc_id,
                        state={
                            "status": "failed",
                            "started_at": doc_started_at,
                            "failed_at": utc_now_isoformat(),
                            "error_message": last_segment_error,
                        },
                    )
                else:
                    await _write_metadata_extraction_state(
                        db_session,
                        graph_id=graph_id,
                        document_id=doc_id,
                        state={
                            "status": "completed",
                            "started_at": doc_started_at,
                            "completed_at": utc_now_isoformat(),
                            "fields_count": len(storage),
                        },
                    )

                docs_seen += 1
                if docs_seen % _METADATA_HEARTBEAT_INTERVAL == 0:
                    logger.info(
                        "Metadata extraction heartbeat graph=%s approach=document "
                        "docs_seen=%d processed=%d skipped=%d errors=%d elapsed=%.0fs",
                        graph_id,
                        docs_seen,
                        processed_documents,
                        skipped_documents,
                        errors,
                        time.monotonic() - loop_start,
                    )

            offset += len(batch)

        return {
            "approach": approach,
            "processed_documents": processed_documents,
            "processed_chunks": processed_chunks,
            "skipped_documents": skipped_documents,
            "skipped_chunks": skipped_chunks,
            "errors": errors,
        }

    # approach == "chunks"
    #
    # We intentionally process per-document (read chunks -> commit -> call LLM -> write -> commit)
    # to avoid long-running DB transactions and server-side cursors.
    doc_id_filter_chunks = (
        "AND d.id = ANY(CAST(:document_ids AS uuid[]))"
        if document_ids is not None
        else ""
    )
    docs_res = await db_session.execute(
        text(
            f"""
            SELECT
                d.id::text AS id
            FROM {docs_tbl} d
            WHERE EXISTS (
                SELECT 1 FROM {chunks_tbl} c WHERE c.document_id = d.id
            )
            {doc_id_filter_chunks}
            ORDER BY d.created_at DESC
            """
        ),
        {"document_ids": document_ids} if document_ids is not None else {},
    )
    docs_rows = docs_res.mappings().all()
    await db_session.commit()  # close read transaction before LLM work

    total_docs = len(docs_rows)
    docs_seen = 0
    loop_start = time.monotonic()

    for drow in docs_rows:
        doc_id = str(drow.get("id") or "").strip()
        if not doc_id:
            continue

        # Fetch all chunk contents for this document (short read transaction)
        chunks_res = await db_session.execute(
            text(
                f"""
                SELECT
                    COALESCE(NULLIF(embedded_content, ''), NULLIF(content, '')) AS content
                FROM {chunks_tbl}
                WHERE document_id = CAST(:doc_id AS uuid)
                ORDER BY index NULLS FIRST, created_at
                """
            ),
            {"doc_id": doc_id},
        )
        chunk_values = chunks_res.scalars().all()
        await db_session.commit()  # close transaction before LLM calls

        if not chunk_values:
            skipped_documents += 1
            continue

        doc_started_at = utc_now_isoformat()
        await _write_metadata_extraction_state(
            db_session,
            graph_id=graph_id,
            document_id=doc_id,
            state={"status": "running", "started_at": doc_started_at},
        )

        storage: dict[str, Any] = {}
        discovery_values: dict[str, list[Any]] = {}
        had_any_chunk_content = False
        chunk_errors = 0
        last_chunk_error: str | None = None

        for cval in chunk_values:
            content_str = str(cval or "").strip()
            if not content_str:
                skipped_chunks += 1
                continue

            had_any_chunk_content = True
            processed_chunks += 1

            try:
                extracted = await _extract_metadata_from_content(
                    prompt_template_system_name=prompt_template_system_name,
                    schema=schema,
                    content=content_str,
                )
            except Exception as exc:  # noqa: BLE001
                errors += 1
                chunk_errors += 1
                last_chunk_error = str(exc)
                logger.warning(
                    "Metadata extraction failed for graph %s doc %s chunk: %s",
                    str(graph_id),
                    doc_id,
                    exc,
                )
                continue

            if not extracted:
                continue

            for raw_k, v in extracted.items():
                k = str(raw_k or "").strip()
                if not k:
                    continue
                _append_discovery_value(discovery_values, key=k, value=v)
                _merge_storage_value(storage, key=k, value=v)

        if not had_any_chunk_content:
            skipped_documents += 1
            # Clear the "running" state we wrote above to avoid stale UI state.
            await _write_metadata_extraction_state(
                db_session,
                graph_id=graph_id,
                document_id=doc_id,
                state={
                    "status": "skipped",
                    "started_at": doc_started_at,
                    "completed_at": utc_now_isoformat(),
                },
            )
            continue

        processed_documents += 1

        if storage:
            await _upsert_document_llm_metadata(
                db_session,
                graph_id=graph_id,
                document_id=doc_id,
                llm_metadata=storage,
            )

        discovery_metadata = _build_discovery_metadata(discovery_values)
        if discovery_metadata:
            await accumulate_extracted_metadata_fields(
                db_session,
                graph_id=graph_id,
                metadata=discovery_metadata,
                extraction_field_settings=extraction_field_settings,
            )

        await db_session.commit()

        if chunk_errors and not storage:
            await _write_metadata_extraction_state(
                db_session,
                graph_id=graph_id,
                document_id=doc_id,
                state={
                    "status": "failed",
                    "started_at": doc_started_at,
                    "failed_at": utc_now_isoformat(),
                    "error_message": last_chunk_error,
                },
            )
        else:
            await _write_metadata_extraction_state(
                db_session,
                graph_id=graph_id,
                document_id=doc_id,
                state={
                    "status": "completed",
                    "started_at": doc_started_at,
                    "completed_at": utc_now_isoformat(),
                    "fields_count": len(storage),
                },
            )

        docs_seen += 1
        if docs_seen % _METADATA_HEARTBEAT_INTERVAL == 0:
            logger.info(
                "Metadata extraction heartbeat graph=%s approach=chunks "
                "progress=%d/%d processed_chunks=%d errors=%d elapsed=%.0fs",
                graph_id,
                docs_seen,
                total_docs,
                processed_chunks,
                errors,
                time.monotonic() - loop_start,
            )

    return {
        "approach": approach,
        "processed_documents": processed_documents,
        "processed_chunks": processed_chunks,
        "skipped_documents": skipped_documents,
        "skipped_chunks": skipped_chunks,
        "errors": errors,
    }
