from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import (
    Float,
    Index,
    MetaData,
    bindparam,
    delete,
    func,
    insert,
    or_,
    select,
    text,
    type_coerce,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphDocument,
    chunks_index_prefix,
    chunks_table_name,
    docs_table_name,
    knowledge_graph_chunk_table,
    knowledge_graph_document_table,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphChunkListResponse,
)

from ..schemas import ChunkSearchResult


class KnowledgeGraphChunkService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID, vector_size: int
    ) -> None:
        """Create the per-graph chunks table + indexes if missing.

        Note: documents table must exist first due to FK.
        """

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        index_prefix = chunks_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            knowledge_graph_document_table(md, docs_name, vector_size=None)
            chunks_tbl = knowledge_graph_chunk_table(
                md, chunks_name, docs_table=docs_name, vector_size=vector_size
            )
            chunks_tbl.create(sync_conn, checkfirst=True)
            Index(f"{index_prefix}_document_id", chunks_tbl.c.document_id).create(
                sync_conn, checkfirst=True
            )

        await conn.run_sync(_create)

    async def drop_table(self, db_session: AsyncSession, *, graph_id: UUID) -> None:
        """Drop the per-graph chunks table if it exists."""

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            chunks_tbl = knowledge_graph_chunk_table(
                md, chunks_name, docs_table=docs_name, vector_size=None
            )
            chunks_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def insert_chunks_bulk(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        document: dict[str, Any],
        chunks: list[KnowledgeGraphChunk],
    ) -> None:
        """Insert chunks for a document into the per-graph chunks table.

        Notes:
        - Uses the caller-provided `db_session` and participates in the surrounding
          transaction (caller controls commit/rollback).
        - Chunks are `KnowledgeGraphChunk` objects; we persist their fields into the
          dynamic per-graph chunks table.
        - If `chunk.content_embedding` is missing/empty, we store NULL (chunk will not
          be returned by similarity search which filters on non-null embeddings).
        """

        if not chunks:
            return

        doc_id_raw = document.get("id")
        if not doc_id_raw:
            raise ValueError("document.id is required to insert chunks")
        doc_id: UUID = (
            doc_id_raw if isinstance(doc_id_raw, UUID) else UUID(str(doc_id_raw))
        )

        docs_tbl_name = docs_table_name(graph_id)
        chunks_tbl_name = chunks_table_name(graph_id)

        md = MetaData()
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            chunks_tbl_name,
            docs_table=docs_tbl_name,
            vector_size=None,
        )

        document_name = str(document.get("name") or "")
        rows: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            # Some sources (e.g. Fluid Topics TOPIC chunks) do not have a page concept
            # and will pass `page=None`. `dict.get()` returns None even when a default
            # is provided if the key exists, so we normalize explicitly here.
            page_val = chunk.page
            page: int | None = (
                page_val if isinstance(page_val, int) and page_val > 0 else None
            )

            embedding_val = chunk.content_embedding
            embedding: list[float] | None = (
                embedding_val
                if isinstance(embedding_val, list) and len(embedding_val) > 0
                else None
            )

            chunk_type_val = chunk.chunk_type
            chunk_type = (
                str(chunk_type_val).strip() if chunk_type_val is not None else ""
            ) or "TEXT"

            rows.append(
                {
                    "name": f"{document_name}_chunk_{idx + 1}",
                    "index": idx,
                    "generated_id": chunk.generated_id,
                    "title": chunk.title or "",
                    "toc_reference": chunk.toc_reference or "",
                    "page": page,
                    "content": chunk.content or "",
                    "content_format": chunk.content_format,
                    "embedded_content": chunk.embedded_content or "",
                    "content_embedding": embedding,
                    "chunk_type": chunk_type,
                    "document_id": doc_id,
                }
            )

        if not rows:
            return

        await db_session.execute(insert(chunks_tbl), rows)

    async def search_chunks(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vector: list[float],
        limit: int,
        only_doc_ids: list[str] | None = None,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[ChunkSearchResult]:
        """Similarity search over per-graph chunks."""

        docs_table = docs_table_name(graph_id)
        chunks_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            chunks_table,
            docs_table=docs_table,
            vector_size=None,
        )
        # IMPORTANT: `findDocumentsByMetadata` compiles a raw SQL predicate that
        # references the documents table as alias `d` (e.g. `d.metadata ...`).
        # When reusing that predicate here, we must ensure the documents table is
        # present in the FROM clause with the same alias, otherwise Postgres will
        # raise "missing FROM-clause entry for table d".
        docs_alias = docs_tbl.alias("d")

        qvec = bindparam("qvec", type_=chunks_tbl.c.content_embedding.type)
        distance_expr = chunks_tbl.c.content_embedding.op("<=>")(qvec)
        score_expr = (1 - type_coerce(distance_expr, Float)).label("score")

        stmt = (
            select(
                chunks_tbl.c.id.label("id"),
                chunks_tbl.c.title.label("title"),
                chunks_tbl.c.content.label("content"),
                chunks_tbl.c.document_id.label("document_id"),
                docs_alias.c.name.label("document_name"),
                docs_alias.c.title.label("document_title"),
                docs_alias.c.external_link.label("document_external_link"),
                chunks_tbl.c.page.label("page"),
                chunks_tbl.c.index.label("index"),
                score_expr,
            )
            .select_from(
                chunks_tbl.join(docs_alias, docs_alias.c.id == chunks_tbl.c.document_id)
            )
            .where(chunks_tbl.c.content_embedding.is_not(None))
            .order_by(score_expr.desc())
            .limit(int(limit))
        )

        if only_doc_ids:
            stmt = stmt.where(
                chunks_tbl.c.document_id.in_([UUID(str(x)) for x in only_doc_ids])
            )

        if doc_filter_where_sql:
            stmt = stmt.where(text(str(doc_filter_where_sql)))

        exec_params: dict[str, Any] = {"qvec": query_vector}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            exec_params.update(doc_filter_where_params)

        rows = (await db_session.execute(stmt, exec_params)).mappings().all()
        return [
            ChunkSearchResult(
                chunk=KnowledgeGraphChunk(
                    id=r["id"],
                    title=r.get("title"),
                    content=r.get("content"),
                    document_id=r.get("document_id"),
                    document=KnowledgeGraphDocument(
                        id=r.get("document_id"),
                        name=r.get("document_name"),
                        title=r.get("document_title"),
                        external_link=r.get("document_external_link"),
                    ),
                    page=r.get("page"),
                    index=r.get("index"),
                ),
                score=float(r["score"]) if r.get("score") is not None else None,
            )
            for r in rows
        ]

    async def list_chunks(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        document_id: UUID | None = None,
    ) -> KnowledgeGraphChunkListResponse:
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

        where_conditions = []
        if document_id is not None:
            where_conditions.append(chunks_tbl.c.document_id == document_id)
        if q:
            q_like = f"%{q}%"
            where_conditions.append(
                or_(
                    chunks_tbl.c.title.ilike(q_like),
                    chunks_tbl.c.name.ilike(q_like),
                    chunks_tbl.c.embedded_content.ilike(q_like),
                )
            )

        join_from = chunks_tbl.join(docs_tbl, docs_tbl.c.id == chunks_tbl.c.document_id)

        count_stmt = select(func.count()).select_from(join_from)
        if where_conditions:
            count_stmt = count_stmt.where(*where_conditions)
        total_count = int((await db_session.execute(count_stmt)).scalar() or 0)

        stmt = (
            select(
                chunks_tbl.c.id.label("id"),
                chunks_tbl.c.name.label("name"),
                chunks_tbl.c.title.label("title"),
                chunks_tbl.c.toc_reference.label("toc_reference"),
                chunks_tbl.c.page.label("page"),
                chunks_tbl.c.chunk_type.label("chunk_type"),
                chunks_tbl.c.content.label("content"),
                chunks_tbl.c.content_format.label("content_format"),
                chunks_tbl.c.created_at.label("created_at"),
                docs_tbl.c.id.label("document_id"),
                docs_tbl.c.name.label("document_name"),
                docs_tbl.c.external_link.label("document_external_link"),
            )
            .select_from(join_from)
            .order_by(
                docs_tbl.c.created_at.desc(),
                chunks_tbl.c.page.nullsfirst(),
                chunks_tbl.c.created_at,
            )
            .limit(int(limit))
            .offset(int(offset))
        )
        if where_conditions:
            stmt = stmt.where(*where_conditions)

        rows_all = (await db_session.execute(stmt)).mappings().all()

        chunks: list[KnowledgeGraphChunkExternalSchema] = []
        for row in rows_all:
            chunk = KnowledgeGraphChunk.from_mapping(row)
            chunks.append(
                KnowledgeGraphChunkExternalSchema(
                    id=str(chunk.id) if chunk.id else "",
                    document_id=str(row.get("document_id") or ""),
                    document_name=str(row.get("document_name") or ""),
                    name=chunk.name,
                    title=chunk.title,
                    toc_reference=chunk.toc_reference,
                    page=chunk.page,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    content_format=chunk.content_format,
                    external_link=row.get("document_external_link") or None,
                    created_at=chunk.created_at.isoformat()
                    if chunk.created_at
                    else None,
                )
            )

        return KnowledgeGraphChunkListResponse(
            chunks=chunks, total=total_count, limit=limit, offset=offset
        )

    async def delete_chunks(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        document_id: UUID | None = None,
    ) -> None:
        md = MetaData()
        chunks_table = knowledge_graph_chunk_table(
            md,
            chunks_table_name(graph_id),
            docs_table=docs_table_name(graph_id),
            vector_size=None,
        )

        conditions = []
        if document_id is not None:
            conditions.append(chunks_table.c.document_id == document_id)

        await db_session.execute(delete(chunks_table).where(*conditions))
        await db_session.commit()
