from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from openai_model.utils import get_model_by_system_name
from stores.pgvector_db import pgvector_client

from .content_config_services import get_graph_embedding_model

logger = logging.getLogger(__name__)


def graph_suffix(graph_id: UUID | str) -> str:
    """Return a safe table name suffix for a graph id."""
    s = str(graph_id)
    return s.replace("-", "_")


def docs_table_name(graph_id: UUID | str) -> str:
    """Per-graph documents table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_documents"


def chunks_table_name(graph_id: UUID | str) -> str:
    """Per-graph chunks table name."""
    return f"knowledge_graph_{graph_suffix(graph_id)}_chunks"


async def _resolve_vector_size(embedding_model: str | None) -> int:
    """Resolve vector size for a given embedding model, defaulting to 1536."""
    if not embedding_model:
        return 1536
    try:
        model_cfg = await get_model_by_system_name(embedding_model)
        cfgs = (model_cfg or {}).get("configs") or {}
        if isinstance(cfgs, dict):
            size = cfgs.get("vector_size")
            if isinstance(size, int) and size > 0:
                return size
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to resolve vector size for model %s: %s", embedding_model, exc
        )
    return 1536


async def ensure_graph_tables_exist(
    db_session: AsyncSession, graph_id: UUID | str
) -> None:
    """Lazily create per-graph documents and chunks tables if missing."""
    docs_table = docs_table_name(graph_id)
    chunks_table = chunks_table_name(graph_id)

    # Check if documents table exists (via pgvector_client)
    docs_exists = bool(
        await pgvector_client.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = $1
            )
            """,
            docs_table,
        )
    )
    if docs_exists:
        return

    logger.info("Resolving selected embedding model vector size for graph %s", graph_id)

    # Determine vector size for embeddings from graph settings -> embedding model configs
    vector_size = 1536
    try:
        embedding_model = await get_graph_embedding_model(
            db_session, graph_id
        )  # model from graph settings.indexing.embedding_model
        if embedding_model:
            model_cfg = await get_model_by_system_name(embedding_model)
            cfgs = (model_cfg or {}).get("configs") or {}
            if isinstance(cfgs, dict):
                vsize = cfgs.get("vector_size")
                if isinstance(vsize, int) and vsize > 0:
                    vector_size = vsize
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to resolve vector size for graph %s: %s. Falling back to %s",
            graph_id,
            exc,
            vector_size,
        )

    logger.info("Creating per-graph tables for graph %s", graph_id)

    # Create documents table
    await pgvector_client.execute_command(
        f"""
        CREATE TABLE IF NOT EXISTS {docs_table} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            source_id UUID NULL REFERENCES knowledge_graph_sources(id) ON DELETE SET NULL,
            type VARCHAR(100),
            content_profile VARCHAR(100),
            title VARCHAR(500),
            summary TEXT,
            summary_embedding vector({vector_size}),
            toc JSONB,
            status VARCHAR(50) DEFAULT 'pending',
            status_message TEXT,
            total_pages INTEGER,
            processing_time DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Indexes for documents
    await pgvector_client.execute_command(
        f"CREATE INDEX IF NOT EXISTS idx_{docs_table}_name ON {docs_table}(name)"
    )
    await pgvector_client.execute_command(
        f"CREATE INDEX IF NOT EXISTS idx_{docs_table}_source_id ON {docs_table}(source_id)"
    )

    # Create chunks table

    await pgvector_client.execute_command(
        f"""
        CREATE TABLE IF NOT EXISTS {chunks_table} (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            index INTEGER,
            generated_id VARCHAR(1000),
            title VARCHAR(500),
            toc_reference VARCHAR(500),
            page INTEGER,
            text TEXT,
            text_embedding vector({vector_size}),
            chunk_type VARCHAR(50),
            document_id UUID NULL REFERENCES {docs_table}(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # Index for chunks
    await pgvector_client.execute_command(
        f"CREATE INDEX IF NOT EXISTS idx_{chunks_table}_document_id ON {chunks_table}(document_id)"
    )
    logger.info("Created per-graph tables for graph %s", graph_id)


async def drop_graph_tables(db_session: AsyncSession, graph_id: UUID) -> None:
    """Drop per-graph chunks and documents tables if they exist."""
    chunks_table = chunks_table_name(graph_id)
    docs_table = docs_table_name(graph_id)
    # Drop chunks first due to FK
    await pgvector_client.execute_command(f"DROP TABLE IF EXISTS {chunks_table}")
    await pgvector_client.execute_command(f"DROP TABLE IF EXISTS {docs_table}")


async def search_documents(
    graph_id: UUID | str,
    query_vector: list[float],
    limit: int,
) -> list[dict[str, Any]]:
    """Similarity search over per-graph documents using summary embeddings."""
    docs_tbl = docs_table_name(graph_id)
    rows = await pgvector_client.execute_query(
        f"""
        SELECT
            d.id::text AS id,
            COALESCE(NULLIF(d.title, ''), d.name) AS title,
            d.summary AS summary,
            1 - (d.summary_embedding <=> $1) AS score
        FROM {docs_tbl} d
        WHERE d.summary_embedding IS NOT NULL
        ORDER BY score DESC
        LIMIT $2
        """,
        query_vector,
        int(limit),
    )
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "content": r["summary"],
            "score": float(r["score"]) if r["score"] is not None else 0.0,
        }
        for r in rows
    ]


async def search_chunks(
    graph_id: UUID | str,
    query_vector: list[float],
    limit: int,
    only_doc_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Similarity search over per-graph chunks."""
    docs_tbl = docs_table_name(graph_id)
    chunks_tbl = chunks_table_name(graph_id)

    where_clause = "c.text_embedding IS NOT NULL"
    params: list[Any] = [query_vector, int(limit)]
    if only_doc_ids:
        where_clause += " AND c.document_id = ANY($3::uuid[])"
        params.append(only_doc_ids)

    rows = await pgvector_client.execute_query(
        f"""
        SELECT
            c.id::text AS id,
            c.title AS title,
            c.text AS text,
            c.document_id::text AS document_id,
            c.page AS page,
            c.index AS index,
            1 - (c.text_embedding <=> $1) AS score
        FROM {chunks_tbl} c
        JOIN {docs_tbl} d ON d.id = c.document_id
        WHERE {where_clause}
        ORDER BY score DESC
        LIMIT $2
        """,
        *params,
    )
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "content": r["text"],
            "document_id": r["document_id"],
            "page": r["page"],
            "index": r["index"],
            "score": float(r["score"]) if r["score"] is not None else 0.0,
        }
        for r in rows
    ]


async def upsert_document_summary(
    graph_id: UUID | str,
    doc_id: str,
    *,
    title: str | None,
    summary: str | None,
    summary_embedding: list[float] | None,
    toc_json: dict | list | None,
) -> None:
    """Update document title/summary/embedding/toc atomically."""
    docs_tbl = docs_table_name(graph_id)
    await pgvector_client.execute_command(
        f"""
        UPDATE {docs_tbl}
        SET title = $1,
            summary = $2,
            summary_embedding = $3,
            toc = $4,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $5
        """,
        title,
        summary,
        summary_embedding,
        toc_json,
        doc_id,
    )


async def insert_chunks_bulk(
    graph_id: UUID | str,
    document: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> int:
    """Insert chunks with embeddings using a single transaction on the pool."""
    if not chunks:
        return 0

    chunks_tbl = chunks_table_name(graph_id)

    await pgvector_client._ensure_pool_initialized()
    if not pgvector_client.pool:
        raise RuntimeError("PgVector connection pool is not initialized")

    inserted = 0
    async with pgvector_client.pool.acquire() as connection:
        async with connection.transaction():
            for idx, chunk_data in enumerate(chunks):
                # Some sources (e.g. Fluid Topics TOPIC chunks) do not have a page concept
                # and will pass `page=None`. `dict.get()` returns None even when a default
                # is provided if the key exists, so we normalize explicitly here.
                page_val = chunk_data.get("page")
                page: int | None = (
                    page_val if isinstance(page_val, int) and page_val > 0 else None
                )

                embedding_val = chunk_data.get("embedding")
                embedding = embedding_val if isinstance(embedding_val, list) else []

                chunk_type_val = chunk_data.get("type")
                chunk_type = (
                    str(chunk_type_val).strip() if chunk_type_val is not None else ""
                ) or "TEXT"

                await connection.execute(
                    f"""
                    INSERT INTO {chunks_tbl} (
                        name, index, title, toc_reference, page, text, text_embedding, chunk_type, document_id
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9
                    )
                    """,
                    f"{document.get('name')}_chunk_{idx + 1}",
                    idx,
                    chunk_data.get("title", ""),
                    chunk_data.get("toc_reference", ""),
                    page,
                    chunk_data.get("text", ""),
                    embedding,
                    chunk_type,
                    document["id"],
                )
                inserted += 1
    return inserted
