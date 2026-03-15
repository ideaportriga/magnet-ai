from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import Column, DateTime, MetaData, String, Table, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .utils import to_uuid


@dataclass(slots=True)
class KnowledgeGraphEdgeRecord:
    """Python representation of a row in a per-graph edges table."""

    id: UUID | None = None
    source_node_id: UUID | None = None
    source_node_type: str = "entity"
    target_node_id: UUID | None = None
    target_node_type: str = ""
    label: str = ""
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else None,
            "source_node_id": str(self.source_node_id)
            if self.source_node_id is not None
            else None,
            "source_node_type": self.source_node_type,
            "target_node_id": str(self.target_node_id)
            if self.target_node_id is not None
            else None,
            "target_node_type": self.target_node_type,
            "label": self.label,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> KnowledgeGraphEdgeRecord:
        source_node_type_val = row.get("source_node_type")
        target_node_type_val = row.get("target_node_type")
        label_val = row.get("label")
        metadata_val = row.get("metadata")
        metadata = metadata_val if isinstance(metadata_val, dict) else None

        return cls(
            id=to_uuid(row.get("id")),
            source_node_id=to_uuid(row.get("source_node_id")),
            source_node_type=str(source_node_type_val)
            if source_node_type_val is not None
            else "entity",
            target_node_id=to_uuid(row.get("target_node_id")),
            target_node_type=str(target_node_type_val)
            if target_node_type_val is not None
            else "",
            label=str(label_val) if label_val is not None else "",
            metadata=metadata,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def knowledge_graph_edge_table(metadata: MetaData, table_name: str) -> Table:
    """Internal SQLAlchemy Core `Table` builder for per-graph edges tables."""

    return Table(
        table_name,
        metadata,
        Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        Column("source_node_id", PG_UUID(as_uuid=True), nullable=False),
        Column(
            "source_node_type",
            String(50),
            nullable=False,
            server_default=text("'entity'"),
        ),
        Column("target_node_id", PG_UUID(as_uuid=True), nullable=False),
        Column("target_node_type", String(50), nullable=False),
        Column("label", String(255), nullable=False, server_default=text("''")),
        Column(
            "metadata",
            JSONB,
            nullable=True,
            server_default=text("'{}'::jsonb"),
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
