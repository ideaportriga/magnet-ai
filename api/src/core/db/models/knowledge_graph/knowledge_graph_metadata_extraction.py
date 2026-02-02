from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID, JsonB
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .knowledge_graph import KnowledgeGraph


class KnowledgeGraphMetadataExtraction(UUIDv7AuditBase):
    """A metadata field definition for extraction within a knowledge graph.

    Unlike `KnowledgeGraphMetadataDiscovery` (which stores *observed* fields tied to a
    source + origin), this model stores extraction-oriented field configuration for
    the graph itself (schema-like configuration).
    """

    __tablename__ = "knowledge_graph_metadata_extractions"
    __table_args__ = (
        UniqueConstraint(
            "graph_id",
            "name",
            name="uq_knowledge_graph_metadata_extractions_name",
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
        back_populates="extracted_metadata_fields",
    )

    # Field identity
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Metadata field name",
    )

    # Field configuration
    settings: Mapped[dict[str, Any]] = mapped_column(
        JsonB,
        nullable=False,
        comment="Metadata field settings",
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
