from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .knowledge_graph_source import KnowledgeGraphSource
    from .knowledge_graph import KnowledgeGraph
    from .knowledge_graph_chunk import KnowledgeGraphChunk


class KnowledgeGraphDocument(UUIDv7AuditBase):
    """Knowledge Graph Document table for storing document metadata."""

    __tablename__ = "knowledge_graph_documents"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Source name",
    )

    # Foreign key to parent graph
    graph_id: Mapped[Optional[UUID]] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graphs.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to knowledge_graphs",
    )

    # Relationship to graph
    graph: Mapped[Optional["KnowledgeGraph"]] = relationship(
        "KnowledgeGraph",
        back_populates="documents",
    )

    # Foreign key to source
    source_id: Mapped[Optional[UUID]] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graph_sources.id", ondelete="SET NULL"),
        nullable=True,
        comment="Foreign key to knowledge_graph_sources",
    )

    # Relationship to source
    source: Mapped[Optional["KnowledgeGraphSource"]] = relationship(
        "KnowledgeGraphSource",
        foreign_keys=[source_id],
    )

    # Document type (e.g., 'pdf', 'doc')
    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Document type (e.g., 'pdf', 'doc')",
    )

    # Content profile name
    content_profile: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Content profile name used for ingestion",
    )

    # Document title
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Document title",
    )

    # Document summary
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Document summary",
    )

    # Document table of contents
    toc: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Document table of contents",
    )

    # Embedding vector for the document
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Embedding vector for the document",
    )

    # Processing status
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="pending",
        comment="Processing status (pending, processing, completed, error)",
    )

    # Processing status message
    status_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Processing status message",
    )

    # Total number of pages in the document
    total_pages: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total number of pages in the document",
    )

    # Processing time in seconds
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Processing time in seconds",
    )

    # Relationship to chunks
    chunks: Mapped[list[KnowledgeGraphChunk]] = relationship(
        "KnowledgeGraphChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
