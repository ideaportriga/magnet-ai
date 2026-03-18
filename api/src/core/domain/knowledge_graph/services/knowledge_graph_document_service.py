from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import PurePath
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import (
    Float,
    Index,
    MetaData,
    bindparam,
    delete,
    func,
    select,
    text,
    type_coerce,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphDocument,
    KnowledgeGraphSource,
    chunks_table_name,
    docs_index_prefix,
    docs_table_name,
    knowledge_graph_chunk_table,
    knowledge_graph_document_table,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphDocumentDetailSchema,
    KnowledgeGraphDocumentExternalSchema,
)
from services.knowledge_graph.utils import normalize_metadata_value

logger = logging.getLogger(__name__)


class KnowledgeGraphDocumentService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID, vector_size: int
    ) -> None:
        """Create the per-graph documents table + indexes if missing."""

        docs_name = docs_table_name(graph_id)
        index_prefix = docs_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            docs_tbl = knowledge_graph_document_table(
                md, docs_name, vector_size=vector_size
            )
            docs_tbl.create(sync_conn, checkfirst=True)
            Index(f"{index_prefix}_name", docs_tbl.c.name).create(
                sync_conn, checkfirst=True
            )
            Index(f"{index_prefix}_source_id", docs_tbl.c.source_id).create(
                sync_conn, checkfirst=True
            )
            # Composite index for efficient sync queries by source + external document ID
            Index(
                f"{index_prefix}_source_doc_id",
                docs_tbl.c.source_id,
                docs_tbl.c.source_document_id,
            ).create(sync_conn, checkfirst=True)

        await conn.run_sync(_create)

    async def drop_table(self, db_session: AsyncSession, *, graph_id: UUID) -> None:
        """Drop the per-graph documents table if it exists.

        Note: chunks table must be dropped first due to FK.
        """

        docs_name = docs_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            docs_tbl = knowledge_graph_document_table(md, docs_name, vector_size=None)
            docs_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def list_documents(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDocumentExternalSchema]:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )
        sources_tbl = KnowledgeGraphSource.__table__

        chunks_count_sq = (
            select(func.count())
            .select_from(chunks_tbl)
            .where(chunks_tbl.c.document_id == docs_tbl.c.id)
            .scalar_subquery()
        )

        stmt = (
            select(
                docs_tbl.c.id.label("id"),
                docs_tbl.c.name.label("name"),
                docs_tbl.c.type.label("type"),
                docs_tbl.c.content_profile.label("content_profile"),
                docs_tbl.c.status.label("status"),
                docs_tbl.c.status_message.label("status_message"),
                docs_tbl.c.title.label("title"),
                docs_tbl.c.total_pages.label("total_pages"),
                docs_tbl.c.processing_time.label("processing_time"),
                docs_tbl.c.created_at.label("created_at"),
                docs_tbl.c.updated_at.label("updated_at"),
                docs_tbl.c.external_link.label("external_link"),
                sources_tbl.c.name.label("source_name"),
                chunks_count_sq.label("chunks_count"),
            )
            .select_from(
                docs_tbl.outerjoin(
                    sources_tbl, sources_tbl.c.id == docs_tbl.c.source_id
                )
            )
            .order_by(docs_tbl.c.created_at.desc())
        )

        rows_all = (await db_session.execute(stmt)).mappings().all()
        documents: list[KnowledgeGraphDocumentExternalSchema] = []
        for row in rows_all:
            doc = KnowledgeGraphDocument.from_mapping(row)
            documents.append(
                KnowledgeGraphDocumentExternalSchema(
                    id=str(doc.id) if doc.id else "",
                    name=doc.name,
                    type=doc.type,
                    content_profile=doc.content_profile,
                    status=doc.status,
                    status_message=doc.status_message,
                    title=doc.title,
                    total_pages=doc.total_pages,
                    processing_time=doc.processing_time,
                    external_link=doc.external_link,
                    chunks_count=int(row.get("chunks_count") or 0),
                    source_name=(row.get("source_name") or None),
                    created_at=doc.created_at.isoformat() if doc.created_at else None,
                    updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                )
            )

        return documents

    async def get_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> KnowledgeGraphDocumentDetailSchema:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )

        chunks_count_sq = (
            select(func.count())
            .select_from(chunks_tbl)
            .where(chunks_tbl.c.document_id == docs_tbl.c.id)
            .scalar_subquery()
        )

        stmt = (
            select(
                docs_tbl.c.id.label("id"),
                docs_tbl.c.name.label("name"),
                docs_tbl.c.type.label("type"),
                docs_tbl.c.content_profile.label("content_profile"),
                docs_tbl.c.title.label("title"),
                docs_tbl.c.summary.label("summary"),
                docs_tbl.c.toc.label("toc"),
                docs_tbl.c.metadata.label("metadata"),
                docs_tbl.c.status.label("status"),
                docs_tbl.c.status_message.label("status_message"),
                docs_tbl.c.total_pages.label("total_pages"),
                docs_tbl.c.processing_time.label("processing_time"),
                docs_tbl.c.external_link.label("external_link"),
                docs_tbl.c.created_at.label("created_at"),
                docs_tbl.c.updated_at.label("updated_at"),
                chunks_count_sq.label("chunks_count"),
            )
            .select_from(docs_tbl)
            .where(docs_tbl.c.id == document_id)
        )
        row = (await db_session.execute(stmt)).mappings().one_or_none()
        if not row:
            raise NotFoundException("Document not found")

        doc = KnowledgeGraphDocument.from_mapping(row)
        return KnowledgeGraphDocumentDetailSchema(
            id=str(doc.id) if doc.id else "",
            name=doc.name,
            type=doc.type,
            content_profile=doc.content_profile,
            title=doc.title,
            summary=doc.summary,
            toc=doc.toc,  # type: ignore[arg-type]
            status=doc.status,
            status_message=doc.status_message,
            total_pages=doc.total_pages,
            processing_time=doc.processing_time,
            external_link=doc.external_link,
            metadata=doc.metadata.to_dict() if doc.metadata else None,
            source_id=None,
            chunks_count=int(row.get("chunks_count") or 0),
            created_at=doc.created_at.isoformat() if doc.created_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
        )

    async def query_documents(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        limit: int | None = 1,
        columns: tuple[str, ...] | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Query per-graph documents by arbitrary document fields.

        - Filters with value `None` are ignored.
        - `columns` defaults to `("id",)`.
        - Returns a list of row mappings (UUID values are normalized to strings).
        """

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(
            md, docs_table_name(graph_id), vector_size=None
        )

        allowed_cols = set(docs_tbl.c.keys())

        requested_filter_cols = set(filters.keys())
        unknown_filter_cols = requested_filter_cols - allowed_cols
        if unknown_filter_cols:
            bad = ", ".join(sorted(unknown_filter_cols))
            raise ValueError(f"Unknown document filter fields: {bad}")

        effective_filters = {k: v for k, v in filters.items() if v is not None}
        if not effective_filters:
            return []

        if columns is None:
            columns = ("id",)
        unknown_columns = set(columns) - allowed_cols
        if unknown_columns:
            bad = ", ".join(sorted(unknown_columns))
            raise ValueError(f"Unknown document columns requested: {bad}")

        stmt = select(*[docs_tbl.c[c] for c in columns]).select_from(docs_tbl)

        for field_name, value in effective_filters.items():
            if field_name in {"id", "source_id"} and isinstance(value, str):
                try:
                    value = UUID(str(value))
                except Exception:  # noqa: BLE001
                    pass
            stmt = stmt.where(docs_tbl.c[field_name] == value)

        if limit is not None:
            stmt = stmt.limit(int(limit))

        rows = (await db_session.execute(stmt)).mappings().all()

        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            for k, v in list(d.items()):
                if isinstance(v, UUID):
                    d[k] = str(v)
            out.append(d)

        return out

    async def search_documents(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vector: list[float],
        limit: int,
        min_score: float = 0.0,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Similarity search over per-graph documents using summary embeddings."""

        docs_table = docs_table_name(graph_id)
        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)

        # Alias for metadata filtering consistency (similar to chunk search)
        docs_alias = docs_tbl.alias("d")

        qvec = bindparam("qvec", type_=docs_alias.c.summary_embedding.type)
        distance_expr = docs_alias.c.summary_embedding.op("<=>")(qvec)
        score_expr = (1 - type_coerce(distance_expr, Float)).label("score")

        title_expr = func.coalesce(
            func.nullif(docs_alias.c.title, ""),
            docs_alias.c.name,
        ).label("title")

        stmt = (
            select(
                docs_alias.c.id.label("id"),
                title_expr,
                docs_alias.c.summary.label("summary"),
                docs_alias.c.external_link.label("external_link"),
                score_expr,
            )
            .select_from(docs_alias)
            .where(docs_alias.c.summary_embedding.is_not(None))
            .order_by(score_expr.desc())
            .limit(int(limit))
        )

        if doc_filter_where_sql:
            stmt = stmt.where(text(str(doc_filter_where_sql)))

        exec_params: dict[str, Any] = {"qvec": query_vector}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            exec_params.update(doc_filter_where_params)

        rows = (await db_session.execute(stmt, exec_params)).mappings().all()

        return [
            {
                "id": str(r.get("id") or ""),
                "title": r.get("title"),
                "content": r.get("summary"),
                "external_link": r.get("external_link"),
                "score": float(r["score"]) if r.get("score") is not None else 0.0,
            }
            for r in rows
            if float(r.get("score") or 0.0) >= min_score
        ]

    async def upsert_document(
        self,
        db_session: AsyncSession,
        source: KnowledgeGraphSource,
        *,
        filename: str,
        total_pages: int | None = None,
        file_metadata: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        default_document_type: str = "txt",
        content_profile: str | None = None,
        source_document_id: str | None = None,
        source_modified_at: datetime | None = None,
        content_hash: str | None = None,
        title: str | None = None,
        external_link: str | None = None,
        toc: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not filename:
            raise ClientException("Filename is required")

        base_name = PurePath(filename).name
        file_ext = base_name.rsplit(".", 1)[-1].lower() if "." in base_name else ""

        doc_metadata_json: str | None = None
        doc_metadata_payload: dict[str, Any] = {}
        if isinstance(file_metadata, dict) and file_metadata:
            doc_metadata_payload["file"] = file_metadata
        if isinstance(source_metadata, dict) and source_metadata:
            doc_metadata_payload["source"] = source_metadata
        if doc_metadata_payload:
            try:
                normalized_payload = normalize_metadata_value(doc_metadata_payload)
                doc_metadata_json = json.dumps(
                    normalized_payload, ensure_ascii=False, default=str
                )
            except Exception:  # noqa: BLE001
                # Best-effort: do not fail document creation if metadata cannot be serialized.
                doc_metadata_json = None

        toc_json: str | None = None
        if toc is not None:
            try:
                toc_json = json.dumps(toc, ensure_ascii=False, default=str)
            except Exception:  # noqa: BLE001
                # Best-effort: do not fail document creation if TOC cannot be serialized.
                toc_json = None

        docs_table = docs_table_name(source.graph_id)

        # Check for existing document - prioritize source_document_id (stable identifier)
        # over name (which can change if file is renamed)
        document_id = None

        if source_document_id:
            # First try to find by source_document_id (the stable unique identifier from the source)
            existing = await db_session.execute(
                text(
                    f"""
                    SELECT id::text
                    FROM {docs_table}
                    WHERE source_id = :sid AND source_document_id = :source_doc_id
                    LIMIT 1
                    """
                ),
                {"sid": str(source.id), "source_doc_id": source_document_id},
            )
            document_id = existing.scalar_one_or_none()

        if not document_id:
            # Fall back to searching by name (for sources that don't provide stable IDs)
            existing = await db_session.execute(
                text(
                    f"""
                    SELECT id::text
                    FROM {docs_table}
                    WHERE source_id = :sid AND name = :name
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"sid": str(source.id), "name": base_name},
            )
            document_id = existing.scalar_one_or_none()
        if document_id:
            await db_session.execute(
                text(
                    f"""
                    UPDATE {docs_table}
                    SET status = 'pending',
                    status_message = NULL,
                    total_pages = :total_pages,
                    type = :type,
                    content_profile = :content_profile,
                    title = COALESCE(:title, title),
                    external_link = COALESCE(:external_link, external_link),
                    toc = CASE
                        WHEN CAST(:toc_json AS jsonb) IS NULL THEN toc
                        ELSE CAST(:toc_json AS jsonb)
                    END,
                    metadata = CASE
                        WHEN CAST(:metadata_json AS jsonb) IS NULL THEN metadata
                        ELSE COALESCE(metadata, '{{}}'::jsonb) || CAST(:metadata_json AS jsonb)
                    END,
                    processing_time = NULL,
                    source_document_id = :source_document_id,
                    source_modified_at = :source_modified_at,
                    content_hash = :content_hash,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {
                    "id": document_id,
                    "total_pages": total_pages,
                    "type": (file_ext or default_document_type),
                    "content_profile": content_profile,
                    "metadata_json": doc_metadata_json,
                    "source_document_id": source_document_id,
                    "source_modified_at": source_modified_at,
                    "content_hash": content_hash,
                    "title": title,
                    "external_link": external_link,
                    "toc_json": toc_json,
                },
            )
            await db_session.commit()
        else:
            res = await db_session.execute(
                text(
                    f"""
                    INSERT INTO {docs_table} (
                    name, type, status, total_pages, source_id, content_profile, metadata,
                    source_document_id, source_modified_at, content_hash,
                    title, toc, external_link
                    )
                    VALUES (
                        :name,
                        :type,
                        'pending',
                        :total_pages,
                        :source_id,
                        :content_profile,
                        COALESCE(CAST(:metadata_json AS jsonb), '{{}}'::jsonb),
                        :source_document_id,
                        :source_modified_at,
                        :content_hash,
                        :title,
                        CAST(:toc_json AS jsonb),
                        :external_link
                    )
                    RETURNING id::text
                    """
                ),
                {
                    "name": base_name,
                    "type": (file_ext or default_document_type),
                    "total_pages": total_pages,
                    "source_id": str(source.id),
                    "content_profile": content_profile,
                    "metadata_json": doc_metadata_json,
                    "source_document_id": source_document_id,
                    "source_modified_at": source_modified_at,
                    "content_hash": content_hash,
                    "title": title,
                    "external_link": external_link,
                    "toc_json": toc_json,
                },
            )
            document_id = res.scalar_one()
            await db_session.commit()

        await self._refresh_documents_count(db_session, source)

        return {"id": document_id, "graph_id": str(source.graph_id), "name": base_name}

    async def update_document(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        document_id: UUID | str,
        fields: dict[str, Any],
        touch_updated_at: bool = True,
        auto_commit: bool = True,
        raise_if_missing: bool = False,
    ) -> bool:
        md = MetaData()
        docs_tbl = knowledge_graph_document_table(
            md, docs_table_name(graph_id), vector_size=None
        )

        allowed_cols = set(docs_tbl.c.keys())
        immutable_cols = {"id", "created_at"}

        requested_cols = set(fields.keys())
        unknown_cols = requested_cols - allowed_cols
        forbidden_cols = requested_cols & immutable_cols
        if unknown_cols or forbidden_cols:
            bad = sorted(unknown_cols | forbidden_cols)
            raise ValueError(f"Cannot update document fields: {', '.join(bad)}")

        update_values: dict[str, Any] = dict(fields)
        if touch_updated_at and "updated_at" not in update_values:
            update_values["updated_at"] = text("CURRENT_TIMESTAMP")

        # Guard against accidental no-ops (e.g. only touching updated_at).
        if not {k for k in update_values.keys() if k != "updated_at"}:
            return False

        doc_uuid: UUID = (
            document_id if isinstance(document_id, UUID) else UUID(str(document_id))
        )

        stmt = (
            update(docs_tbl)
            .where(docs_tbl.c.id == doc_uuid)
            .values(**update_values)
            .returning(docs_tbl.c.id)
        )

        try:
            res = await db_session.execute(stmt)
            updated_id = res.scalar_one_or_none()
            if auto_commit:
                await db_session.commit()
        except Exception:
            if auto_commit:
                # Keep session usable for best-effort callers.
                try:
                    await db_session.rollback()
                except Exception:  # noqa: BLE001
                    pass
            raise

        if updated_id is None and raise_if_missing:
            raise NotFoundException("Document not found")

        return updated_id is not None

    async def update_document_metadata_only(
        self,
        db_session: AsyncSession,
        source: KnowledgeGraphSource,
        *,
        document_id: str,
        filename: str | None = None,
        source_document_id: str | None = None,
        source_modified_at: datetime | None = None,
        file_metadata: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        content_profile: str | None = None,
        title: str | None = None,
        external_link: str | None = None,
    ) -> None:
        """Update all non-content fields without re-processing chunks or embeddings.

        Every supplied value overwrites the stored value.  ``None`` preserves whatever
        is already in the database (via ``COALESCE``), so callers only need to pass
        the fields they actually have.
        """

        docs_table = docs_table_name(source.graph_id)

        doc_metadata_json: str | None = None
        doc_metadata_payload: dict[str, Any] = {}
        if isinstance(file_metadata, dict) and file_metadata:
            doc_metadata_payload["file"] = file_metadata
        if isinstance(source_metadata, dict) and source_metadata:
            doc_metadata_payload["source"] = source_metadata
        if doc_metadata_payload:
            try:
                doc_metadata_json = json.dumps(
                    normalize_metadata_value(doc_metadata_payload),
                    ensure_ascii=False,
                    default=str,
                )
            except Exception:  # noqa: BLE001
                pass  # best-effort

        await db_session.execute(
            text(
                f"""
                UPDATE {docs_table}
                SET
                    name                = COALESCE(:name, name),
                    source_document_id  = COALESCE(:source_document_id, source_document_id),
                    source_modified_at  = COALESCE(:source_modified_at, source_modified_at),
                    title               = COALESCE(:title, title),
                    external_link       = COALESCE(:external_link, external_link),
                    content_profile     = COALESCE(:content_profile, content_profile),
                    metadata            = CASE
                                            WHEN CAST(:metadata_json AS jsonb) IS NULL THEN metadata
                                            ELSE COALESCE(metadata, '{{}}'::jsonb) || CAST(:metadata_json AS jsonb)
                                          END,
                    updated_at          = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": document_id,
                "name": PurePath(filename).name if filename else None,
                "source_document_id": source_document_id,
                "source_modified_at": source_modified_at,
                "title": title,
                "external_link": external_link,
                "content_profile": content_profile,
                "metadata_json": doc_metadata_json,
            },
        )
        await db_session.commit()

    async def _refresh_documents_count(
        self, db_session: AsyncSession, source: KnowledgeGraphSource
    ):
        try:
            table = docs_table_name(source.graph_id)
            res = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE source_id = :sid"),
                {"sid": str(source.id)},
            )
            source.documents_count = int(res.scalar_one() or 0)
            await db_session.commit()
        except Exception:
            logger.warning(
                "Failed to update documents_count for source %s", str(source.id)
            )

    async def delete_document(
        self, db_session: AsyncSession, graph_id: UUID, id: UUID
    ) -> None:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )

        # Explicitly delete chunks first
        await db_session.execute(
            delete(chunks_tbl).where(chunks_tbl.c.document_id == id)
        )

        # Then delete the document row
        res = await db_session.execute(
            delete(docs_tbl).where(docs_tbl.c.id == id).returning(1)
        )
        deleted = res.scalar_one_or_none()
        await db_session.commit()
        if not deleted:
            raise NotFoundException("Document not found")
