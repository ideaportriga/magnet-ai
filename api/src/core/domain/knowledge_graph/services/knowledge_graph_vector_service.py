from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Float,
    Index,
    MetaData,
    bindparam,
    func,
    insert,
    select,
    text,
    type_coerce,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphDocument,
    chunks_table_name,
    docs_table_name,
    knowledge_graph_chunk_table,
    knowledge_graph_chunk_vector_table,
    knowledge_graph_document_table,
    vec_index_prefix,
    vec_table_name,
)
from core.db.models.knowledge_graph.utils import graph_suffix
from core.domain.knowledge_graph.schemas import ChunkSearchResult

logger = logging.getLogger(__name__)


class KnowledgeGraphVectorService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str, vector_size: int
    ) -> None:
        """Create the per-graph chunk vectors table + indexes if missing.

        Note: the chunks table must exist first due to FK.
        """

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        table_name = vec_table_name(graph_id, vector_size)
        index_prefix = vec_index_prefix(graph_id, vector_size)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            # Register chunks table in metadata for the FK reference
            knowledge_graph_chunk_table(md, chunks_name, docs_table=docs_name)
            vec_tbl = knowledge_graph_chunk_vector_table(
                md, table_name, chunks_table=chunks_name, vector_size=vector_size
            )
            vec_tbl.create(sync_conn, checkfirst=True)
            Index(f"{index_prefix}_chunk_id", vec_tbl.c.chunk_id).create(
                sync_conn, checkfirst=True
            )
            Index(
                f"{index_prefix}_chunk_ct",
                vec_tbl.c.chunk_id,
                vec_tbl.c.content_type,
            ).create(sync_conn, checkfirst=True)

        await conn.run_sync(_create)

    async def drop_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str, vector_size: int
    ) -> None:
        """Drop a specific per-graph chunk vectors table if it exists."""

        chunks_name = chunks_table_name(graph_id)
        table_name = vec_table_name(graph_id, vector_size)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            vec_tbl = knowledge_graph_chunk_vector_table(
                md, table_name, chunks_table=chunks_name, vector_size=None
            )
            vec_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def drop_all_vec_tables(
        self, db_session: AsyncSession, *, graph_id: UUID | str
    ) -> None:
        """Drop all vector tables for a graph (any vector dimension)."""

        suffix = graph_suffix(graph_id)
        prefix = f"knowledge_graph_{suffix}_"
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop_all(sync_conn) -> None:
            from sqlalchemy import inspect as sa_inspect

            insp = sa_inspect(sync_conn)
            for tbl_name in insp.get_table_names():
                if (
                    isinstance(tbl_name, str)
                    and tbl_name.startswith(prefix)
                    and tbl_name.endswith("_vec")
                ):
                    sync_conn.execute(
                        text(f'DROP TABLE IF EXISTS "{tbl_name}" CASCADE')
                    )

        await conn.run_sync(_drop_all)

    async def insert_vectors_bulk(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        vector_size: int,
        chunk_ids: list[UUID],
        embedding_map: dict[int, list[tuple[str, list[float]]]] | None = None,
    ) -> None:
        """Insert vector records for the given chunks into the per-graph vec table.

        ``embedding_map`` maps chunk list-indices to their ``(text, vector)``
        tuples produced by the embedding step.  Chunks with a single part use
        ``content_type="chunk_content"``; chunks with multiple parts use
        ``content_type="chunk_content_part"`` for each row.
        """

        if not chunk_ids:
            return

        chunks_name = chunks_table_name(graph_id)
        table_name = vec_table_name(graph_id, vector_size)

        md = MetaData()
        vec_tbl = knowledge_graph_chunk_vector_table(
            md, table_name, chunks_table=chunks_name, vector_size=None
        )

        parts_map = embedding_map or {}

        rows: list[dict[str, Any]] = []
        for idx, chunk_id in enumerate(chunk_ids):
            indexing_parts = parts_map.get(idx)
            if not indexing_parts:
                continue

            content_type = (
                "chunk_content" if len(indexing_parts) == 1 else "chunk_content_part"
            )
            for part_text, part_vector in indexing_parts:
                if not isinstance(part_vector, list) or len(part_vector) == 0:
                    continue
                rows.append(
                    {
                        "chunk_id": chunk_id,
                        "content_type": content_type,
                        "content": part_text,
                        "vector": part_vector,
                    }
                )

        if not rows:
            return

        await db_session.execute(insert(vec_tbl), rows)

    async def search_vectors(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        vector_size: int,
        query_vector: list[float],
        limit: int,
        only_doc_ids: list[str] | None = None,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[ChunkSearchResult]:
        """Similarity search over the per-graph vector table.

        When a chunk has multiple vector rows (e.g. fixed-size parts), each
        row is scored independently and the **best** (highest) score per chunk
        is returned.  This way a single chunk never appears more than once in
        the results.
        """

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        table_name = vec_table_name(graph_id, vector_size)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_name, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(md, chunks_name, docs_table=docs_name)
        vec_tbl = knowledge_graph_chunk_vector_table(
            md, table_name, chunks_table=chunks_name, vector_size=None
        )

        docs_alias = docs_tbl.alias("d")

        # Score each vector row: 1 - cosine_distance.
        qvec = bindparam("qvec", type_=vec_tbl.c.vector.type)
        distance_expr = vec_tbl.c.vector.op("<=>")(qvec)
        score_expr = 1 - type_coerce(distance_expr, Float)

        # Sub-query: for each chunk pick the best score across all its
        # vector rows (whole content OR individual parts).
        best_score_sq = (
            select(
                vec_tbl.c.chunk_id.label("chunk_id"),
                func.max(score_expr).label("best_score"),
            )
            .group_by(vec_tbl.c.chunk_id)
            .subquery("best_scores")
        )

        # Main query: join best scores → chunks → documents.
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
                best_score_sq.c.best_score.label("score"),
            )
            .select_from(
                best_score_sq.join(
                    chunks_tbl, chunks_tbl.c.id == best_score_sq.c.chunk_id
                ).join(docs_alias, docs_alias.c.id == chunks_tbl.c.document_id)
            )
            .order_by(best_score_sq.c.best_score.desc())
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
