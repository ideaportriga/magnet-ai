from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .knowledge_graph import KnowledgeGraph


class KnowledgeGraphSource(UUIDv7AuditBase):
    """Knowledge Graph Source for external data sources (SharePoint, etc.)."""

    __tablename__ = "knowledge_graph_sources"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Source name",
    )

    # Foreign key to parent graph
    graph_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to knowledge_graphs",
    )

    # Relationship to graph
    graph: Mapped["KnowledgeGraph"] = relationship(
        "KnowledgeGraph",
        back_populates="sources",
    )

    # Source type (e.g., 'sharepoint', 'confluence', 'upload')
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Source type (e.g., 'sharepoint', 'confluence', 'upload')",
    )

    # Source configuration (connection details, credentials, etc.)
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Source configuration (connection details, credentials, etc.)",
    )

    # Status of the source (active, syncing, error)
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Source status",
    )

    # Number of documents from this source
    documents_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="Number of documents from this source",
    )

    # Last sync timestamp
    last_sync_at: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Last sync timestamp",
    )
