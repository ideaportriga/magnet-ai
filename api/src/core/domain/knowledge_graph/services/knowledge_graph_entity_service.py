from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import Index, MetaData, delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphEntityRecord,
    entities_index_prefix,
    entities_table_name,
    knowledge_graph_entity_table,
)
from services.knowledge_graph.utils import normalize_metadata_value


def normalize_record_identifier(value: str | None) -> str:
    """Normalize entity identifiers for deduplication.

    The normalization is intentionally conservative: it keeps alphanumeric
    content, harmonizes punctuation/spacing, and case-folds the result.
    """

    raw = unicodedata.normalize("NFKC", str(value or "")).strip()
    if not raw:
        return ""

    normalized = raw.casefold()
    normalized = (
        normalized.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    normalized = re.sub(r"[\s\-_./|]+", " ", normalized)
    normalized = re.sub(r"[\"'`]+", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,.;:-")
    return normalized


def _normalize_stringish(value: Any) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).strip())


def _value_is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _value_signature(value: Any) -> str:
    if isinstance(value, str):
        return f"str:{normalize_record_identifier(value) or _normalize_stringish(value).casefold()}"
    try:
        return json.dumps(normalize_metadata_value(value), sort_keys=True, default=str)
    except Exception:  # noqa: BLE001
        return repr(value)


def _string_richness_score(value: str) -> tuple[int, int, int]:
    normalized = _normalize_stringish(value)
    alnum_count = len(re.sub(r"[^0-9A-Za-z]+", "", normalized))
    has_mixed_case = int(
        any(ch.isupper() for ch in normalized)
        and any(ch.islower() for ch in normalized)
    )
    return (alnum_count, has_mixed_case, len(normalized))


def _prefer_identifier_display(existing: str, candidate: str) -> str:
    existing_value = _normalize_stringish(existing)
    candidate_value = _normalize_stringish(candidate)
    if not existing_value:
        return candidate_value
    if not candidate_value:
        return existing_value
    if _string_richness_score(candidate_value) > _string_richness_score(existing_value):
        return candidate_value
    return existing_value


def _merge_string_lists(
    existing: list[str] | None, incoming: list[str] | None
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in [*(existing or []), *(incoming or [])]:
        normalized = _normalize_stringish(value)
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _merge_scalar_values(existing: Any, incoming: Any) -> Any:
    if _value_is_empty(existing):
        return incoming
    if _value_is_empty(incoming):
        return existing

    if _value_signature(existing) == _value_signature(incoming):
        if isinstance(existing, str) and isinstance(incoming, str):
            return _prefer_identifier_display(existing, incoming)
        return existing

    if isinstance(existing, list):
        merged = list(existing)
        seen = {_value_signature(value) for value in merged}
        incoming_values = incoming if isinstance(incoming, list) else [incoming]
        for value in incoming_values:
            signature = _value_signature(value)
            if signature not in seen:
                merged.append(value)
                seen.add(signature)
        return merged

    if isinstance(incoming, list):
        return _merge_scalar_values(incoming, existing)

    if isinstance(existing, str) and isinstance(incoming, str):
        existing_norm = normalize_record_identifier(existing)
        incoming_norm = normalize_record_identifier(incoming)
        if existing_norm and existing_norm == incoming_norm:
            return _prefer_identifier_display(existing, incoming)

        preferred = _prefer_identifier_display(existing, incoming)
        alternate = incoming if preferred == existing else existing
        return [preferred, alternate]

    return [existing, incoming]


def _merge_column_values(
    existing: Mapping[str, Any] | None, incoming: Mapping[str, Any] | None
) -> dict[str, Any]:
    merged: dict[str, Any] = normalize_metadata_value(dict(existing or {}))
    for key, value in dict(incoming or {}).items():
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        incoming_value = normalize_metadata_value(value)
        if normalized_key not in merged:
            if not _value_is_empty(incoming_value):
                merged[normalized_key] = incoming_value
            continue
        merged[normalized_key] = _merge_scalar_values(
            merged.get(normalized_key), incoming_value
        )
    return merged


class KnowledgeGraphEntityService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str
    ) -> None:
        """Create the per-graph entities table + indexes if missing."""

        table_name = entities_table_name(graph_id)
        index_prefix = entities_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            entities_tbl = knowledge_graph_entity_table(md, table_name)
            entities_tbl.create(sync_conn, checkfirst=True)
            for statement in (
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS normalized_record_identifier VARCHAR(500) NOT NULL DEFAULT ''",
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS identifier_aliases JSONB NOT NULL DEFAULT '[]'::jsonb",
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS source_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb",
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS source_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb",
            ):
                sync_conn.execute(text(statement))
            sync_conn.execute(
                text(
                    f"""
                    UPDATE {table_name}
                    SET normalized_record_identifier = LOWER(BTRIM(record_identifier))
                    WHERE COALESCE(normalized_record_identifier, '') = ''
                    """
                )
            )
            Index(f"{index_prefix}_entity", entities_tbl.c.entity).create(
                sync_conn, checkfirst=True
            )
            sync_conn.execute(text(f'DROP INDEX IF EXISTS "{index_prefix}_erid_uq"'))
            Index(
                f"{index_prefix}_nrid_uq",
                entities_tbl.c.entity,
                entities_tbl.c.normalized_record_identifier,
                unique=True,
            ).create(sync_conn, checkfirst=True)
            Index(
                f"{index_prefix}_cols_gin",
                entities_tbl.c.column_values,
                postgresql_using="gin",
            ).create(sync_conn, checkfirst=True)

        await conn.run_sync(_create)

    async def drop_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str
    ) -> None:
        """Drop the per-graph entities table if it exists."""

        table_name = entities_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            entities_tbl = knowledge_graph_entity_table(md, table_name)
            entities_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def list_entity_types(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
    ) -> list[dict[str, Any]]:
        """Return distinct entity names with their record counts."""

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        stmt = (
            select(
                entities_tbl.c.entity,
                func.count().label("count"),
            )
            .group_by(entities_tbl.c.entity)
            .order_by(entities_tbl.c.entity)
        )

        rows = (await db_session.execute(stmt)).mappings().all()
        return [{"entity": row["entity"], "count": row["count"]} for row in rows]

    async def delete_records(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity: str | None = None,
    ) -> int:
        """Delete entity rows for a graph, optionally scoped to one entity type."""

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        entity_value = str(entity or "").strip()
        if entity is not None and not entity_value:
            raise ClientException("Entity name is required")

        stmt = delete(entities_tbl)
        if entity_value:
            stmt = stmt.where(entities_tbl.c.entity == entity_value)

        deleted_rows = (
            (await db_session.execute(stmt.returning(entities_tbl.c.id)))
            .scalars()
            .all()
        )
        await db_session.commit()
        return len(deleted_rows)

    async def delete_record(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        record_id: UUID | str,
    ) -> None:
        """Delete one entity row from a graph."""

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)
        record_id_value = (
            record_id if isinstance(record_id, UUID) else UUID(str(record_id))
        )

        deleted_id = (
            await db_session.execute(
                delete(entities_tbl)
                .where(entities_tbl.c.id == record_id_value)
                .returning(entities_tbl.c.id)
            )
        ).scalar_one_or_none()
        await db_session.commit()
        if deleted_id is None:
            raise NotFoundException("Entity record not found")

    async def count_records(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity: str | None = None,
    ) -> int:
        """Count entity rows, optionally filtered by entity name."""

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        stmt = select(func.count()).select_from(entities_tbl)

        entity_value = str(entity or "").strip()
        if entity_value:
            stmt = stmt.where(entities_tbl.c.entity == entity_value)

        result = await db_session.execute(stmt)
        return result.scalar_one()

    async def list_records(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity: str | None = None,
        record_identifier: str | None = None,
        column_values_contains: Mapping[str, Any] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeGraphEntityRecord]:
        """List per-graph entity rows with optional JSONB containment filters."""

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        stmt = (
            select(entities_tbl)
            .order_by(
                entities_tbl.c.updated_at.desc(),
                entities_tbl.c.created_at.desc(),
                entities_tbl.c.id.desc(),
            )
            .limit(max(int(limit), 1))
            .offset(max(int(offset), 0))
        )

        entity_value = str(entity or "").strip()
        if entity_value:
            stmt = stmt.where(entities_tbl.c.entity == entity_value)

        record_identifier_value = str(record_identifier or "").strip()
        if record_identifier_value:
            stmt = stmt.where(
                entities_tbl.c.record_identifier == record_identifier_value
            )

        if isinstance(column_values_contains, Mapping) and column_values_contains:
            stmt = stmt.where(
                entities_tbl.c.column_values.contains(column_values_contains)
            )

        rows = (await db_session.execute(stmt)).mappings().all()
        return [KnowledgeGraphEntityRecord.from_mapping(row) for row in rows]

    async def query_records(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        filter_expr: Any = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[KnowledgeGraphEntityRecord], int]:
        """Query entity records using the filter expression DSL.

        Returns ``(records, total_count)``.
        """

        await self.create_table(db_session, graph_id=graph_id)
        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        from services.knowledge_graph.entity_filter_compiler import (
            EntityFilterCompiler,
        )

        compiler = EntityFilterCompiler(table_name)
        where_sql, params = compiler.compile(filter_expr)

        # Build base queries
        count_stmt = select(func.count()).select_from(entities_tbl)
        data_stmt = (
            select(entities_tbl)
            .order_by(
                entities_tbl.c.updated_at.desc(),
                entities_tbl.c.created_at.desc(),
                entities_tbl.c.id.desc(),
            )
            .limit(max(int(limit), 1))
            .offset(max(int(offset), 0))
        )

        if where_sql:
            where_clause = text(where_sql).bindparams(**params)
            count_stmt = count_stmt.where(where_clause)
            # Re-create the clause for the data query (text() objects are single-use)
            data_stmt = data_stmt.where(text(where_sql).bindparams(**params))

        total = (await db_session.execute(count_stmt)).scalar_one()
        rows = (await db_session.execute(data_stmt)).mappings().all()
        records = [KnowledgeGraphEntityRecord.from_mapping(row) for row in rows]
        return (records, total)

    async def upsert_record(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity: str,
        record_identifier: str,
        column_values: Mapping[str, Any] | None,
        source_document_id: UUID | str | None = None,
        source_chunk_id: UUID | str | None = None,
        source_id: UUID | str | None = None,
    ) -> KnowledgeGraphEntityRecord:
        """Insert or update a per-graph entity row with dedup and provenance."""

        await self.create_table(db_session, graph_id=graph_id)
        entity_value = str(entity or "").strip()
        if not entity_value:
            raise ValueError("entity is required")

        record_identifier_value = str(record_identifier or "").strip()
        if not record_identifier_value:
            raise ValueError("record_identifier is required")

        normalized_record_identifier = normalize_record_identifier(
            record_identifier_value
        )
        if not normalized_record_identifier:
            raise ValueError("normalized_record_identifier is required")

        normalized_column_values = normalize_metadata_value(dict(column_values or {}))
        source_document_id_value = (
            str(source_document_id).strip() if source_document_id is not None else None
        )
        source_chunk_id_value = (
            str(source_chunk_id).strip() if source_chunk_id is not None else None
        )

        table_name = entities_table_name(graph_id)
        md = MetaData()
        entities_tbl = knowledge_graph_entity_table(md, table_name)

        existing_row = (
            (
                await db_session.execute(
                    select(entities_tbl)
                    .where(entities_tbl.c.entity == entity_value)
                    .where(
                        entities_tbl.c.normalized_record_identifier
                        == normalized_record_identifier
                    )
                    .limit(1)
                )
            )
            .mappings()
            .one_or_none()
        )

        if existing_row is None:
            insert_stmt = (
                entities_tbl.insert()
                .values(
                    entity=entity_value,
                    record_identifier=record_identifier_value,
                    normalized_record_identifier=normalized_record_identifier,
                    column_values=normalized_column_values,
                    identifier_aliases=[record_identifier_value],
                    source_document_ids=(
                        [source_document_id_value] if source_document_id_value else []
                    ),
                    source_chunk_ids=(
                        [source_chunk_id_value] if source_chunk_id_value else []
                    ),
                )
                .returning(*entities_tbl.c)
            )
            row = (await db_session.execute(insert_stmt)).mappings().one()
            return KnowledgeGraphEntityRecord.from_mapping(row)

        existing_record = KnowledgeGraphEntityRecord.from_mapping(existing_row)
        merged_record_identifier = _prefer_identifier_display(
            existing_record.record_identifier, record_identifier_value
        )
        merged_column_values = _merge_column_values(
            existing_record.column_values, normalized_column_values
        )
        merged_identifier_aliases = _merge_string_lists(
            existing_record.identifier_aliases, [record_identifier_value]
        )
        merged_source_document_ids = _merge_string_lists(
            existing_record.source_document_ids,
            [source_document_id_value] if source_document_id_value else [],
        )
        merged_source_chunk_ids = _merge_string_lists(
            existing_record.source_chunk_ids,
            [source_chunk_id_value] if source_chunk_id_value else [],
        )

        stmt = (
            update(entities_tbl)
            .where(entities_tbl.c.id == existing_record.id)
            .values(
                record_identifier=merged_record_identifier,
                normalized_record_identifier=normalized_record_identifier,
                column_values=normalize_metadata_value(merged_column_values),
                identifier_aliases=merged_identifier_aliases,
                source_document_ids=merged_source_document_ids,
                source_chunk_ids=merged_source_chunk_ids,
                updated_at=func.now(),
            )
            .returning(*entities_tbl.c)
        )

        row = (await db_session.execute(stmt)).mappings().one()
        return KnowledgeGraphEntityRecord.from_mapping(row)
