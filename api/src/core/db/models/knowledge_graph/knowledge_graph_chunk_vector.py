from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .utils import to_uuid


@dataclass(slots=True)
class KnowledgeGraphChunkVector:
    """Python representation of a row in a per-graph chunk vectors table.

    These tables are created dynamically (one per graph per vector dimension),
    so we do not map them as a single SQLAlchemy ORM model.
    """

    id: UUID | None = None
    chunk_id: UUID | None = None
    content_type: str = "chunk_content"
    content: str | None = None
    vector: list[float] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else None,
            "chunk_id": str(self.chunk_id) if self.chunk_id is not None else None,
            "content_type": self.content_type,
            "content": self.content,
            "vector": self.vector,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> KnowledgeGraphChunkVector:
        vector_val = row.get("vector")
        vector = vector_val if isinstance(vector_val, list) else None

        return cls(
            id=to_uuid(row.get("id")),
            chunk_id=to_uuid(row.get("chunk_id")),
            content_type=str(row.get("content_type") or "chunk_content"),
            content=row.get("content"),
            vector=vector,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def knowledge_graph_chunk_vector_table(
    metadata: MetaData,
    table_name: str,
    *,
    chunks_table: str,
    vector_size: int | None,
) -> Table:
    """SQLAlchemy Core Table builder for per-graph chunk vectors table."""

    vector_type = Vector(int(vector_size)) if vector_size is not None else Vector()
    return Table(
        table_name,
        metadata,
        Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        Column(
            "chunk_id",
            PG_UUID(as_uuid=True),
            ForeignKey(f"{chunks_table}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column(
            "content_type",
            String(100),
            nullable=False,
            server_default=text("'chunk_content'"),
        ),
        Column("content", Text, nullable=True),
        Column("vector", vector_type, nullable=True),
        Column(
            "created_at",
            DateTime(timezone=False),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        Column(
            "updated_at",
            DateTime(timezone=False),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
