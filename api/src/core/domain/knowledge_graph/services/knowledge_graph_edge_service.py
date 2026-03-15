from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Index, MetaData, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphEdgeRecord,
    edges_index_prefix,
    edges_table_name,
    knowledge_graph_edge_table,
)


class KnowledgeGraphEdgeService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str
    ) -> None:
        """Create the per-graph edges table + indexes if missing."""

        table_name = edges_table_name(graph_id)
        index_prefix = edges_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            edges_tbl = knowledge_graph_edge_table(md, table_name)
            edges_tbl.create(sync_conn, checkfirst=True)
            Index(
                f"{index_prefix}_src",
                edges_tbl.c.source_node_id,
                edges_tbl.c.source_node_type,
            ).create(sync_conn, checkfirst=True)
            Index(
                f"{index_prefix}_tgt",
                edges_tbl.c.target_node_id,
                edges_tbl.c.target_node_type,
            ).create(sync_conn, checkfirst=True)
            Index(
                f"{index_prefix}_src_tgt_uq",
                edges_tbl.c.source_node_id,
                edges_tbl.c.source_node_type,
                edges_tbl.c.target_node_id,
                edges_tbl.c.target_node_type,
                unique=True,
            ).create(sync_conn, checkfirst=True)

        await conn.run_sync(_create)

    async def drop_table(
        self, db_session: AsyncSession, *, graph_id: UUID | str
    ) -> None:
        """Drop the per-graph edges table if it exists."""

        table_name = edges_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            edges_tbl = knowledge_graph_edge_table(md, table_name)
            edges_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def upsert_edge(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        source_node_id: UUID,
        source_node_type: str = "entity",
        target_node_id: UUID,
        target_node_type: str,
        label: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeGraphEdgeRecord:
        """Insert or update an edge row using the unique constraint for dedup."""

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        insert_values = {
            "source_node_id": source_node_id,
            "source_node_type": source_node_type,
            "target_node_id": target_node_id,
            "target_node_type": target_node_type,
            "label": label,
            "metadata": metadata or {},
        }

        stmt = pg_insert(edges_tbl).values(**insert_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                edges_tbl.c.source_node_id,
                edges_tbl.c.source_node_type,
                edges_tbl.c.target_node_id,
                edges_tbl.c.target_node_type,
            ],
            set_={
                "label": stmt.excluded.label,
                "metadata": stmt.excluded.metadata,
                "updated_at": func.now(),
            },
        ).returning(*edges_tbl.c)

        row = (await db_session.execute(stmt)).mappings().one()
        return KnowledgeGraphEdgeRecord.from_mapping(row)

    async def delete_edges_for_entity(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity_id: UUID,
    ) -> int:
        """Delete all edges where source_node_id matches the given entity."""

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        result = await db_session.execute(
            delete(edges_tbl)
            .where(edges_tbl.c.source_node_id == entity_id)
            .returning(edges_tbl.c.id)
        )
        return len(result.scalars().all())

    async def delete_edges_for_entities(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity_ids: list[UUID],
    ) -> int:
        """Delete all edges for multiple entities at once."""

        if not entity_ids:
            return 0

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        result = await db_session.execute(
            delete(edges_tbl)
            .where(edges_tbl.c.source_node_id.in_(entity_ids))
            .returning(edges_tbl.c.id)
        )
        return len(result.scalars().all())

    async def list_edges_for_entity(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity_id: UUID,
        target_node_type: str | None = None,
    ) -> list[KnowledgeGraphEdgeRecord]:
        """Get edges for one entity, optionally filtered by target type."""

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        stmt = select(edges_tbl).where(edges_tbl.c.source_node_id == entity_id)
        if target_node_type:
            stmt = stmt.where(edges_tbl.c.target_node_type == target_node_type)
        stmt = stmt.order_by(edges_tbl.c.created_at.desc())

        rows = (await db_session.execute(stmt)).mappings().all()
        return [KnowledgeGraphEdgeRecord.from_mapping(row) for row in rows]

    async def get_target_ids_for_entity(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity_id: UUID,
        target_node_type: str,
    ) -> list[str]:
        """Return flat list of target IDs for an entity and target type."""

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        stmt = (
            select(edges_tbl.c.target_node_id)
            .where(edges_tbl.c.source_node_id == entity_id)
            .where(edges_tbl.c.target_node_type == target_node_type)
        )

        rows = (await db_session.execute(stmt)).scalars().all()
        return [str(r) for r in rows]

    async def get_entity_edge_map(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        entity_ids: list[UUID],
        target_node_type: str | None = None,
    ) -> dict[UUID, list[KnowledgeGraphEdgeRecord]]:
        """Batch fetch edges for multiple entities, grouped by source_node_id."""

        if not entity_ids:
            return {}

        table_name = edges_table_name(graph_id)
        md = MetaData()
        edges_tbl = knowledge_graph_edge_table(md, table_name)

        stmt = select(edges_tbl).where(edges_tbl.c.source_node_id.in_(entity_ids))
        if target_node_type:
            stmt = stmt.where(edges_tbl.c.target_node_type == target_node_type)

        rows = (await db_session.execute(stmt)).mappings().all()

        result: dict[UUID, list[KnowledgeGraphEdgeRecord]] = {
            eid: [] for eid in entity_ids
        }
        for row in rows:
            edge = KnowledgeGraphEdgeRecord.from_mapping(row)
            if edge.source_node_id in result:
                result[edge.source_node_id].append(edge)
        return result
