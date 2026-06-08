from __future__ import annotations

import asyncio
import logging
import time
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
from sqlalchemy.exc import ProgrammingError
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
from core.db.session import async_session_maker
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphChunkListResponse,
)
from services.knowledge_graph.rrf import (
    fusion_diagnostics,
    hybrid_full_text_search,
    hybrid_vector_search,
    merge_attempts_by_max_score,
    normalized_rrf_score,
    reciprocal_rank_fusion,
    vector_literal,
)
from services.observability import observability_context, observe
from services.observability.models import SpanType

from ..schemas import ChunkSearchResult

logger = logging.getLogger(__name__)


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
            # Hybrid retrieval: GIN over the tsvector generated column (full-text).
            Index(
                f"{index_prefix}search_tsv",
                chunks_tbl.c.search_tsv,
                postgresql_using="gin",
            ).create(sync_conn, checkfirst=True)

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

    async def count_chunks(self, db_session: AsyncSession, *, graph_id: UUID) -> int:
        """Return number of chunks in the per-graph chunks table.

        Returns 0 if the table does not exist yet.
        """

        chunks_name = chunks_table_name(graph_id)
        docs_name = docs_table_name(graph_id)
        md = MetaData()
        chunks_tbl = knowledge_graph_chunk_table(
            md, chunks_name, docs_table=docs_name, vector_size=None
        )
        stmt = select(func.count()).select_from(chunks_tbl)
        try:
            result = await db_session.execute(stmt)
        except ProgrammingError:
            await db_session.rollback()
            return 0
        return int(result.scalar() or 0)

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
        search_method: str,
        query_vectors: list[list[float]] | None,
        query_texts: list[str],
        rrf_k: int,
        limit: int,
        candidate_pool: int,
        query_vector_texts: list[str] | None = None,
        only_doc_ids: list[str] | None = None,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[ChunkSearchResult]:
        """Similarity search over per-graph chunks.

        ``search_method`` selects the retrieval strategy:

        - ``"vector"``: pgvector cosine similarity on ``content_embedding``.
          One cosine search per vector in ``query_vectors``, merged by max
          similarity per chunk.
        - ``"full_text"``: tsvector full-text search only, fused via RRF.
        - ``"hybrid"``: parallel pgvector + tsvector full-text fused via RRF.

        For the fused methods, every query variant runs its own sub-query; the
        attempts of each method are merged (dedup by max score) into a single
        ranked list, and only those per-method lists are fused via RRF.

        ``candidate_pool`` is how many rows each fused sub-query fetches before
        RRF fusion (ignored in pure vector mode, which fetches ``limit`` per
        vector).

        ``ChunkSearchResult.score`` carries cosine similarity for vector mode
        and a normalized RRF score in [0, 1] for the fused modes.
        """

        if search_method == "vector":
            return await self._search_chunks_vector(
                db_session,
                graph_id=graph_id,
                query_vectors=query_vectors or [],
                limit=limit,
                only_doc_ids=only_doc_ids,
                doc_filter_where_sql=doc_filter_where_sql,
                doc_filter_where_params=doc_filter_where_params,
            )

        return await self._search_chunks_fused(
            db_session,
            graph_id=graph_id,
            query_vectors=query_vectors,
            query_texts=query_texts,
            query_vector_texts=query_vector_texts,
            limit=limit,
            candidate_pool=candidate_pool,
            only_doc_ids=only_doc_ids,
            doc_filter_where_sql=doc_filter_where_sql,
            doc_filter_where_params=doc_filter_where_params,
            include_vector=(search_method == "hybrid"),
            include_full_text=search_method in ("full_text", "hybrid"),
            rrf_k=rrf_k,
        )

    @observe(
        name="Vector search",
        type=SpanType.SEARCH,
        description="pgvector cosine-similarity search over content/summary embeddings.",
    )
    async def _search_chunks_vector(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vectors: list[list[float]],
        limit: int,
        only_doc_ids: list[str] | None,
        doc_filter_where_sql: str | None,
        doc_filter_where_params: dict[str, Any] | None,
    ) -> list[ChunkSearchResult]:
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

        base_params: dict[str, Any] = {}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            base_params.update(doc_filter_where_params)

        # Run one cosine search per query variant, then keep the best similarity
        # per chunk. A single variant reduces to the original top-`limit` query.
        best_by_id: dict[Any, Any] = {}
        for vector in query_vectors:
            if not vector:
                continue
            rows = (
                (await db_session.execute(stmt, {**base_params, "qvec": vector}))
                .mappings()
                .all()
            )
            for r in rows:
                cid = r["id"]
                score = float(r["score"]) if r.get("score") is not None else None
                existing = best_by_id.get(cid)
                if existing is None or (
                    score is not None
                    and (existing["score"] is None or score > existing["score"])
                ):
                    best_by_id[cid] = {"row": r, "score": score}

        merged = sorted(
            best_by_id.values(),
            key=lambda e: e["score"] if e["score"] is not None else -1.0,
            reverse=True,
        )[: int(limit)]

        observability_context.update_current_span(
            input={"variants": len(query_vectors)}, output={"count": len(merged)}
        )
        results: list[ChunkSearchResult] = []
        for entry in merged:
            r = entry["row"]
            results.append(
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
                    score=entry["score"],
                )
            )
        return results

    async def _search_chunks_fused(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vectors: list[list[float]] | None,
        query_texts: list[str],
        query_vector_texts: list[str] | None,
        limit: int,
        candidate_pool: int,
        only_doc_ids: list[str] | None,
        doc_filter_where_sql: str | None,
        doc_filter_where_params: dict[str, Any] | None,
        include_vector: bool,
        include_full_text: bool,
        rrf_k: int,
    ) -> list[ChunkSearchResult]:
        """Run candidate sub-queries in parallel and fuse with RRF.

        Every query variant contributes its own sub-query (one vector sub-query
        per vector, one tsvector sub-query per text). The
        attempts of each method are first merged into a single ranked list
        (dedup by max relevance score), so multiple variants of one method count
        as a single RRF voter rather than fusing independently. RRF then fuses
        the per-method lists. Sub-queries each use their own AsyncSession so they
        can execute concurrently; a single hydration query then loads full rows
        on the caller's session.
        """

        docs_table = docs_table_name(graph_id)
        chunks_table = chunks_table_name(graph_id)
        candidates = max(int(candidate_pool), 1)

        common_filter_sql = doc_filter_where_sql or None
        common_params: dict[str, Any] = {}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            common_params.update(doc_filter_where_params)

        only_doc_clause = ""
        if only_doc_ids:
            common_params["only_doc_ids"] = [UUID(str(x)) for x in only_doc_ids]
            # asyncpg expands lists when bound with CAST as uuid[]
            only_doc_clause = " AND c.document_id = ANY(CAST(:only_doc_ids AS uuid[]))"

        filter_suffix = (
            f" AND {common_filter_sql}" if common_filter_sql else ""
        ) + only_doc_clause

        join_clause = (
            f"FROM {chunks_table} AS c JOIN {docs_table} AS d ON d.id = c.document_id "
        )

        vector_sql = (
            f"SELECT c.id, 1 - (c.content_embedding <=> CAST(:qvec AS vector)) AS score "
            f"{join_clause}"
            f"WHERE c.content_embedding IS NOT NULL{filter_suffix} "
            f"ORDER BY c.content_embedding <=> CAST(:qvec AS vector) "
            f"LIMIT :cand"
        )
        tsv_sql = (
            f"SELECT c.id, "
            f"ts_rank_cd(c.search_tsv, plainto_tsquery('english', :qtext)) AS score "
            f"{join_clause}"
            f"WHERE c.search_tsv @@ plainto_tsquery('english', :qtext){filter_suffix} "
            f"ORDER BY score DESC "
            f"LIMIT :cand"
        )

        # Build sub-query coroutines grouped by method so the attempts of one
        # method (one per query variant) can be merged before RRF.
        method_coros: dict[str, list[Any]] = {
            "vector": [],
            "full_text": [],
        }
        if include_vector and query_vectors:
            for idx, vector in enumerate(query_vectors):
                if not vector:
                    continue
                vector_text = (
                    query_vector_texts[idx]
                    if query_vector_texts and idx < len(query_vector_texts)
                    else ""
                )
                method_coros["vector"].append(
                    hybrid_vector_search(
                        vector_text,
                        vector_sql,
                        {
                            **common_params,
                            "qvec": vector_literal(vector),
                            "cand": candidates,
                        },
                        session_maker=async_session_maker,
                    )
                )
        for query_text in query_texts or []:
            if not query_text:
                continue
            if include_full_text:
                method_coros["full_text"].append(
                    hybrid_full_text_search(
                        query_text,
                        tsv_sql,
                        {**common_params, "qtext": query_text, "cand": candidates},
                        session_maker=async_session_maker,
                    )
                )

        ordered_methods = [m for m in ("vector", "full_text") if method_coros[m]]
        if not ordered_methods:
            logger.info(
                "hybrid chunks search short-circuit: no contributing sub-queries graph_id=%s",
                graph_id,
            )
            return []

        # Flatten for concurrent execution, remembering each coro's method.
        flat_coros: list[Any] = []
        flat_methods: list[str] = []
        for method in ordered_methods:
            for coro in method_coros[method]:
                flat_coros.append(coro)
                flat_methods.append(method)

        search_mode = "hybrid" if include_vector else "full_text"
        contributing = len(ordered_methods)
        fan_out_started = time.perf_counter()
        logger.info(
            "hybrid chunks search start mode=%s methods=%s attempts=%d candidates=%d limit=%d "
            "rrf_k=%d only_doc_ids=%d graph_id=%s",
            search_mode,
            ordered_methods,
            len(flat_coros),
            candidates,
            limit,
            rrf_k,
            len(only_doc_ids) if only_doc_ids else 0,
            graph_id,
        )

        attempt_results = await asyncio.gather(*flat_coros)
        fan_out_ms = round((time.perf_counter() - fan_out_started) * 1000, 2)

        # Merge the attempts of each method (dedup by max score) into one ranked
        # id list per method, then fuse only those per-method lists with RRF.
        per_method_attempts: dict[str, list[list[tuple[str, float]]]] = {
            m: [] for m in ordered_methods
        }
        for method, result in zip(flat_methods, attempt_results):
            per_method_attempts[method].append(result)

        method_results: dict[str, list[str]] = {
            method: merge_attempts_by_max_score(attempts)
            for method, attempts in per_method_attempts.items()
        }
        rank_lists = [method_results[m] for m in ordered_methods]
        fused = reciprocal_rank_fusion(rank_lists, k=rrf_k)
        diag = fusion_diagnostics(
            method_results=method_results,
            fused=fused,
            num_methods=contributing,
            k=rrf_k,
        )

        logger.info(
            "hybrid chunks fusion mode=%s methods=%s per_method=%s unique=%d overlap=%d fused=%d "
            "fan_out_ms=%.2f top_score=%.4f",
            search_mode,
            ordered_methods,
            diag["per_method_result_count"],
            diag["unique_candidates"],
            diag["multi_method_overlap"],
            diag["fused_total"],
            fan_out_ms,
            diag["top_rrf_score_normalized"],
        )

        if not fused:
            return []

        top = fused[: int(limit)]
        ids_in_order = [item_id for item_id, _ in top]
        score_by_id = {
            item_id: normalized_rrf_score(raw, num_methods=contributing, k=rrf_k)
            for item_id, raw in top
        }

        # Hydrate full rows in the caller's session, preserving order and filters.
        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md, chunks_table, docs_table=docs_table, vector_size=None
        )
        docs_alias = docs_tbl.alias("d")
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
            )
            .select_from(
                chunks_tbl.join(docs_alias, docs_alias.c.id == chunks_tbl.c.document_id)
            )
            .where(chunks_tbl.c.id.in_([UUID(i) for i in ids_in_order]))
        )
        if only_doc_ids:
            stmt = stmt.where(
                chunks_tbl.c.document_id.in_([UUID(str(x)) for x in only_doc_ids])
            )
        if common_filter_sql:
            stmt = stmt.where(text(str(common_filter_sql)))

        rows = (await db_session.execute(stmt, common_params)).mappings().all()
        by_id = {str(r.get("id")): r for r in rows}

        out: list[ChunkSearchResult] = []
        for cid in ids_in_order:
            r = by_id.get(cid)
            if r is None:
                continue
            out.append(
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
                    score=float(score_by_id[cid]),
                )
            )
        return out

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
            vector_size=None,
        )

        conditions = []
        if document_id is not None:
            conditions.append(chunks_table.c.document_id == document_id)

        await db_session.execute(delete(chunks_table).where(*conditions))
        await db_session.commit()
