from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .knowledge_graph_document import KnowledgeGraphDocument


class KnowledgeGraphChunk(UUIDv7AuditBase):
    """Knowledge Graph Chunk table for storing document chunks."""

    __tablename__ = "knowledge_graph_chunks"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Source name",
    )

    # Chunk index
    index: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Chunk index in the document",
    )

    # Generated ID from the AI chunking process (for reference tracking)
    generated_id: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Generated ID from AI chunking process",
    )

    # Chunk title
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Chunk title",
    )

    # TOC reference (for hierarchical structure)
    toc_reference: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="TOC reference",
    )

    # Page number where the chunk starts
    page: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Page number where the chunk starts",
    )

    # Chunk text content
    text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Chunk text content",
    )

    # Embedding vector for the chunk (stored as JSON array)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Embedding vector for the chunk",
    )

    # Chunk type (TEXT, TABLE, etc.)
    chunk_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Chunk type (TEXT, TABLE, etc.)",
    )

    # Foreign key to document
    document_id: Mapped[Optional[UUID]] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graph_documents.id", ondelete="CASCADE"),
        nullable=True,
        comment="Foreign key to knowledge_graph_documents",
    )

    # Relationship to document
    document: Mapped[Optional[KnowledgeGraphDocument]] = relationship(
        "KnowledgeGraphDocument",
        back_populates="chunks",
    )
