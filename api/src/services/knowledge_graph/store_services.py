from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from core.db.models.knowledge_graph import docs_table_name
from stores.pgvector_db import pgvector_client

logger = logging.getLogger(__name__)


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
