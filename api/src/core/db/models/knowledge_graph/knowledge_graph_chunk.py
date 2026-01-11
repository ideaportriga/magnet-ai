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
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .knowledge_graph_document import KnowledgeGraphDocument
from .utils import to_uuid


@dataclass(slots=True)
class KnowledgeGraphChunk:
    """Python representation of a row in a *per-graph* chunks table.

    Notes:
    - These tables are created dynamically (one per graph), so we **do not** map them
      as a single SQLAlchemy ORM `DeclarativeBase` model with a fixed `__tablename__`.
    """

    # PK / FKs
    id: UUID | None = None
    document_id: UUID | None = None

    # Required
    name: str = ""

    # Metadata
    index: int | None = None
    generated_id: str | None = None
    title: str | None = None
    toc_reference: str | None = None
    page: int | None = None
    chunk_type: str | None = None

    # Content
    content: str | None = None
    content_format: str | None = None
    embedded_content: str | None = None
    content_embedding: list[float] | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # References
    document: KnowledgeGraphDocument | None = None

    def to_json(self) -> dict:
        return {
            "id": str(self.id) if self.id is not None else None,
            "name": self.name,
            "index": self.index,
            "generated_id": self.generated_id,
            "title": self.title,
            "toc_reference": self.toc_reference,
            "page": self.page,
            "chunk_type": self.chunk_type,
            "content": self.content,
            "content_format": self.content_format,
            "embedded_content": self.embedded_content,
            "content_embedding": self.content_embedding,
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
            "document": self.document.to_json() if self.document is not None else None,
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> KnowledgeGraphChunk:
        """Create an instance from a mapping (e.g. SQLAlchemy RowMapping)."""

        name_val = row.get("name")
        name = str(name_val) if name_val is not None else ""

        embedding_val = row.get("content_embedding")
        embedding = embedding_val if isinstance(embedding_val, list) else None

        return cls(
            id=to_uuid(row.get("id")),
            document_id=to_uuid(row.get("document_id")),
            name=name,
            index=row.get("index"),
            generated_id=row.get("generated_id"),
            title=row.get("title"),
            toc_reference=row.get("toc_reference"),
            page=row.get("page"),
            content=row.get("content"),
            content_format=row.get("content_format"),
            embedded_content=row.get("embedded_content"),
            content_embedding=embedding,
            chunk_type=row.get("chunk_type"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def knowledge_graph_chunk_table(
    metadata: MetaData, chunks_table: str, *, docs_table: str, vector_size: int | None
) -> Table:
    """Internal SQLAlchemy Core `Table` builder for per-graph chunks table."""

    vector_type = Vector(int(vector_size)) if vector_size is not None else Vector()
    return Table(
        chunks_table,
        metadata,
        Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        Column("name", String(255), nullable=False),
        Column("index", Integer, nullable=True),
        Column("generated_id", String(1000), nullable=True),
        Column("title", String(500), nullable=True),
        Column("toc_reference", String(500), nullable=True),
        Column("page", Integer, nullable=True),
        Column("content", Text, nullable=True),
        Column("content_format", String(100), nullable=True),
        Column("embedded_content", Text, nullable=True),
        Column("content_embedding", vector_type, nullable=True),
        Column("chunk_type", String(50), nullable=True),
        Column(
            "document_id",
            PG_UUID(as_uuid=True),
            ForeignKey(f"{docs_table}.id", ondelete="CASCADE"),
            nullable=True,
        ),
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
