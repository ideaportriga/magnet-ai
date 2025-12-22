from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .knowledge_graph_source import KnowledgeGraphSource
from .utils import to_uuid


@dataclass(slots=True)
class KnowledgeGraphDocument:
    """Python representation of a row in a *per-graph* documents table.

    Notes:
    - These tables are created dynamically (one per graph), so we **do not** map them
      as a single SQLAlchemy ORM `DeclarativeBase` model with a fixed `__tablename__`.
    """

    # PK / FKs
    id: UUID | None = None
    source_id: UUID | None = None

    # Required
    name: str = ""

    # Metadata
    type: str | None = None
    content_profile: str | None = None
    title: str | None = None
    status: str | None = None
    status_message: str | None = None
    total_pages: int | None = None
    processing_time: float | None = None

    # Content
    summary: str | None = None
    toc: dict | list | None = None
    summary_embedding: list[float] | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> KnowledgeGraphDocument:
        """Create an instance from a mapping (e.g. SQLAlchemy RowMapping)."""

        name_val = row.get("name")
        name = str(name_val) if name_val is not None else ""

        embedding_val = row.get("summary_embedding")
        embedding = embedding_val if isinstance(embedding_val, list) else None

        processing_time_val = row.get("processing_time")
        ptime: float | None
        if processing_time_val is None:
            ptime = None
        else:
            try:
                ptime = float(processing_time_val)
            except Exception:  # noqa: BLE001
                ptime = None

        return cls(
            id=to_uuid(row.get("id")),
            source_id=to_uuid(row.get("source_id")),
            name=name,
            type=row.get("type"),
            content_profile=row.get("content_profile"),
            title=row.get("title"),
            summary=row.get("summary"),
            toc=row.get("toc"),
            summary_embedding=embedding,
            status=row.get("status"),
            status_message=row.get("status_message"),
            total_pages=row.get("total_pages"),
            processing_time=ptime,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def knowledge_graph_document_table(
    metadata: MetaData, docs_table: str, *, vector_size: int | None
) -> Table:
    """Internal SQLAlchemy Core `Table` builder for per-graph documents table."""

    vector_type = Vector(int(vector_size)) if vector_size is not None else Vector()
    return Table(
        docs_table,
        metadata,
        Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        Column("name", String(255), nullable=False),
        Column(
            "source_id",
            PG_UUID(as_uuid=True),
            ForeignKey(KnowledgeGraphSource.__table__.c.id, ondelete="SET NULL"),
            nullable=True,
        ),
        Column("type", String(100), nullable=True),
        Column("content_profile", String(100), nullable=True),
        Column("title", String(500), nullable=True),
        Column("summary", Text, nullable=True),
        Column("summary_embedding", vector_type, nullable=True),
        Column("toc", JSONB, nullable=True),
        Column("status", String(50), server_default=text("'pending'"), nullable=True),
        Column("status_message", Text, nullable=True),
        Column("total_pages", Integer, nullable=True),
        Column("processing_time", Float, nullable=True),
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
