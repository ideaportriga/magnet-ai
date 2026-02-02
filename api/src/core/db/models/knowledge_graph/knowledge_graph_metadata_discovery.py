from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .knowledge_graph import KnowledgeGraph
    from .knowledge_graph_source import KnowledgeGraphSource


class KnowledgeGraphMetadataDiscovery(UUIDv7AuditBase):
    """A metadata field discovered for a specific knowledge graph source.

    This table stores *discovered* fields (from native document metadata, ingestion
    source systems) so the UI can list "Discovered Fields" and allow users to
    promote them into the graph's metadata schema (stored in graph settings).
    """

    __tablename__ = "knowledge_graph_metadata_discoveries"
    __table_args__ = (
        UniqueConstraint(
            "graph_id",
            "source_id",
            "origin",
            "name",
            name="uq_knowledge_graph_metadata_discoveries_name",
        ),
    )

    # Parent graph
    graph_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to knowledge_graphs",
    )

    graph: Mapped["KnowledgeGraph"] = relationship(
        "KnowledgeGraph",
        back_populates="discovered_metadata_fields",
    )

    # Parent source (1:M) that observed this discovered field (best-effort attribution)
    source_id: Mapped[UUID] = mapped_column(
        GUID(),
        ForeignKey("knowledge_graph_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to knowledge_graph_sources",
    )

    source: Mapped["KnowledgeGraphSource"] = relationship(
        "KnowledgeGraphSource",
        back_populates="discovered_metadata_fields",
    )

    # Field identity
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Discovered metadata field name",
    )

    # Aggregated observations
    inferred_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Inferred metadata value type (string, number, boolean, date, ...)",
    )

    origin: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Origin where this field was observed (file, source)",
    )

    sample_values: Mapped[Optional[list[str]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Sample values observed for this field (best-effort, limited set)",
    )

    value_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Total number of values observed for this field (best-effort aggregation)",
    )
