from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal
from uuid import UUID

import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import chunks_table_name, docs_table_name
from services.knowledge_graph.metadata_services import (
    accumulate_discovered_metadata_fields,
)
from services.knowledge_graph.models import MetadataMultiValueContainer
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template

logger = logging.getLogger(__name__)

MetadataExtractionApproach = Literal["document", "chunks"]


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


def _to_uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except Exception:
        return None


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
    content: str,
) -> dict[str, Any]:
    # Avoid capturing potentially large/sensitive content in spans; record only sizes/ids.
    try:
        observability_context.update_current_span(
            extra_data={
                "prompt_template_system_name": str(prompt_template_system_name or ""),
                "content_chars": len(str(content or "")),
                "expected_format": "yaml_or_json",
            }
        )
    except Exception:
        pass

    user_content = (
        "Extract metadata from the following content.\n"
        "Return ONLY a YAML mapping or a JSON object (no extra commentary).\n\n"
        f"```text\n{content}\n```"
    )
    result = await execute_prompt_template(
        system_name_or_config=prompt_template_system_name,
        template_additional_messages=[{"role": "user", "content": user_content}],
    )
    return _best_effort_json_object_from_text(result.content)


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
        metadata_json = json.dumps(
            {"llm": llm_metadata}, ensure_ascii=False, default=str
        )
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
    segment_size: int = 18000,
    segment_overlap: float = 0.1,
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

    try:
        observability_context.update_current_span(
            extra_data={
                "graph_id": str(graph_id),
                "approach": str(approach),
                "prompt_template_system_name": prompt_template_system_name,
                "segment_size": int(segment_size),
                "segment_overlap": float(segment_overlap),
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
            # End the read transaction before any LLM calls
            await db_session.commit()

            if not batch:
                break

            for row in batch:
                doc_id = str(row.get("id") or "").strip()
                if not doc_id:
                    continue

                # Fetch content for a single document (short read transaction)
                content_res = await db_session.execute(
                    text(
                        f"""
                        SELECT
                            NULLIF(content_plaintext, '') AS content
                        FROM {docs_tbl}
                        WHERE id = :id\:\:uuid
                        LIMIT 1
                        """
                    ),
                    {"id": doc_id},
                )
                content = content_res.scalar_one_or_none()
                await db_session.commit()  # close transaction before LLM calls

                content_str = str(content or "").strip()
                if not content_str:
                    skipped_documents += 1
                    continue

                processed_documents += 1

                storage: dict[str, Any] = {}
                discovery_values: dict[str, list[Any]] = {}

                segments = _split_into_segments(
                    content_str,
                    segment_size=segment_size,
                    segment_overlap=segment_overlap,
                )
                for segment in segments:
                    try:
                        extracted = await _extract_metadata_from_content(
                            prompt_template_system_name=prompt_template_system_name,
                            content=segment,
                        )
                    except Exception as exc:  # noqa: BLE001
                        errors += 1
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
                    await accumulate_discovered_metadata_fields(
                        db_session,
                        graph_id=graph_id,
                        source_id=_to_uuid_or_none(row.get("source_id")),
                        metadata=discovery_metadata,
                        origin="llm",
                    )

                await db_session.commit()

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
    await db_session.commit()  # close read transaction before LLM work

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
                WHERE document_id = :doc_id::uuid
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

        storage: dict[str, Any] = {}
        discovery_values: dict[str, list[Any]] = {}
        had_any_chunk_content = False

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
                    content=content_str,
                )
            except Exception as exc:  # noqa: BLE001
                errors += 1
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
            await accumulate_discovered_metadata_fields(
                db_session,
                graph_id=graph_id,
                source_id=_to_uuid_or_none(drow.get("source_id")),
                metadata=discovery_metadata,
                origin="llm",
            )

        await db_session.commit()

    return {
        "approach": approach,
        "processed_documents": processed_documents,
        "processed_chunks": processed_chunks,
        "skipped_documents": skipped_documents,
        "skipped_chunks": skipped_chunks,
        "errors": errors,
    }
