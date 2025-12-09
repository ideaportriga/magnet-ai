from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from .knowledge_graph_source import KnowledgeGraphSource


class KnowledgeGraph(UUIDAuditSimpleBase):
    """Knowledge Graph root entity that groups documents."""

    __tablename__ = "knowledge_graphs"

    # Settings for the knowledge graph (processing configuration, etc.)
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Knowledge graph settings (processing config, etc.)",
    )

    # Relationship to sources in this graph
    sources: Mapped[list["KnowledgeGraphSource"]] = relationship(
        "KnowledgeGraphSource",
        back_populates="graph",
        cascade="all, delete-orphan",
    )
