from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import Index, MetaData, insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    chunks_table_name,
    docs_table_name,
    knowledge_graph_chunk_table,
    knowledge_graph_chunk_vector_table,
    vec_index_prefix,
    vec_table_name,
)
from core.db.models.knowledge_graph.utils import graph_suffix

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
            knowledge_graph_chunk_table(
                md, chunks_name, docs_table=docs_name, vector_size=None
            )
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
        chunks: list[KnowledgeGraphChunk],
    ) -> None:
        """Insert vector records for the given chunks into the per-graph vec table.

        ``chunk_ids`` and ``chunks`` must be parallel lists (same length, same order).
        Only chunks with a non-empty ``content_embedding`` are inserted.
        """

        if not chunk_ids or not chunks:
            return

        chunks_name = chunks_table_name(graph_id)
        table_name = vec_table_name(graph_id, vector_size)

        md = MetaData()
        vec_tbl = knowledge_graph_chunk_vector_table(
            md, table_name, chunks_table=chunks_name, vector_size=None
        )

        rows: list[dict[str, Any]] = []
        for chunk_id, chunk in zip(chunk_ids, chunks):
            embedding = chunk.content_embedding
            if not isinstance(embedding, list) or len(embedding) == 0:
                continue
            rows.append(
                {
                    "chunk_id": chunk_id,
                    "content_type": "chunk_content",
                    "content": chunk.embedded_content or chunk.content or "",
                    "vector": embedding,
                }
            )

        if not rows:
            return

        await db_session.execute(insert(vec_tbl), rows)
