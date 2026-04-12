from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import (
    Index,
    MetaData,
    delete,
    func,
    insert,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
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


class KnowledgeGraphChunkService:
    async def create_table(self, db_session: AsyncSession, *, graph_id: UUID) -> None:
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
                md, chunks_name, docs_table=docs_name
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
                md, chunks_name, docs_table=docs_name
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
        vector_size: int | None = None,
        embedding_map: dict[int, list[tuple[str, list[float]]]] | None = None,
    ) -> None:
        """Insert chunks for a document into the per-graph chunks table.

        Notes:
        - Uses the caller-provided `db_session` and participates in the surrounding
          transaction (caller controls commit/rollback).
        - Chunks are `KnowledgeGraphChunk` objects; we persist their fields into the
          dynamic per-graph chunks table.
        - When ``vector_size`` and ``embedding_map`` are provided, vectors are
          written to the separate per-graph vector table.
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
        )

        document_name = str(document.get("name") or "")
        rows: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            page_val = chunk.page
            page: int | None = (
                page_val if isinstance(page_val, int) and page_val > 0 else None
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
                    "chunk_type": chunk_type,
                    "document_id": doc_id,
                }
            )

        if not rows:
            return

        result = await db_session.execute(
            insert(chunks_tbl).returning(chunks_tbl.c.id), rows
        )
        inserted_ids: list[UUID] = [row[0] for row in result.fetchall()]

        if vector_size and inserted_ids:
            from .knowledge_graph_vector_service import KnowledgeGraphVectorService

            vec_svc = KnowledgeGraphVectorService()
            await vec_svc.insert_vectors_bulk(
                db_session,
                graph_id=graph_id,
                vector_size=vector_size,
                chunk_ids=inserted_ids,
                embedding_map=embedding_map,
            )

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
            .order_by(docs_tbl.c.created_at.desc(), chunks_tbl.c.index)
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
        )

        conditions = []
        if document_id is not None:
            conditions.append(chunks_table.c.document_id == document_id)

        await db_session.execute(delete(chunks_table).where(*conditions))
        await db_session.commit()
