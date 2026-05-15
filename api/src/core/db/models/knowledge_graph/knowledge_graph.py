from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User
    from .knowledge_graph_metadata_discovery import KnowledgeGraphMetadataDiscovery
    from .knowledge_graph_metadata_extraction import KnowledgeGraphMetadataExtraction
    from .knowledge_graph_source import KnowledgeGraphSource


class KnowledgeGraph(UUIDAuditSimpleBase):
    """Tenant + record-level scoped knowledge graph (PR 10 rollout)."""

    __tablename__ = "knowledge_graphs"
    __table_args__ = (
        Index(
            "uq_knowledge_graphs_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_knowledge_graphs_tenant_id", "tenant_id"),
        Index("ix_knowledge_graphs_owner_id", "owner_id"),
        Index("ix_knowledge_graphs_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_knowledge_graphs_visibility",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="System name (unique within tenant)",
    )
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="tenant",
        server_default="tenant",
    )

    tenant: Mapped["Tenant"] = relationship(lazy="noload")
    owner: Mapped[Optional["User"]] = relationship(lazy="noload")
    department: Mapped[Optional["Department"]] = relationship(lazy="noload")

    # Settings for the knowledge graph (processing configuration, etc.)
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Knowledge graph settings (processing config, etc.)",
    )

    # Process states for graph operations (extraction status, sync progress, etc.)
    state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Process states for graph operations (extraction status, sync progress, etc.)",
    )

    # Relationship to sources in this graph
    sources: Mapped[list["KnowledgeGraphSource"]] = relationship(
        "KnowledgeGraphSource",
        back_populates="graph",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    # Discovered metadata fields (observed across documents/sources in this graph)
    discovered_metadata_fields: Mapped[list["KnowledgeGraphMetadataDiscovery"]] = (
        relationship(
            "KnowledgeGraphMetadataDiscovery",
            back_populates="graph",
            cascade="all, delete-orphan",
            lazy="noload",
        )
    )

    # Metadata extraction field definitions (graph-level schema/config)
    extracted_metadata_fields: Mapped[list["KnowledgeGraphMetadataExtraction"]] = (
        relationship(
            "KnowledgeGraphMetadataExtraction",
            back_populates="graph",
            cascade="all, delete-orphan",
            lazy="noload",
        )
    )
