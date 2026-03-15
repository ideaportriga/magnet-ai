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
class KnowledgeGraphEntityRecord:
    """Python representation of a row in a per-graph extracted entities table."""

    id: UUID | None = None
    entity: str = ""
    record_identifier: str = ""
    normalized_record_identifier: str = ""
    column_values: dict[str, Any] | None = None
    identifier_aliases: list[str] | None = None
    source_document_ids: list[str] | None = None
    source_chunk_ids: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": str(self.id) if self.id is not None else None,
            "entity": self.entity,
            "record_identifier": self.record_identifier,
            "normalized_record_identifier": self.normalized_record_identifier,
            "column_values": self.column_values or {},
            "identifier_aliases": self.identifier_aliases or [],
            "source_document_ids": self.source_document_ids or [],
            "source_chunk_ids": self.source_chunk_ids or [],
            "created_at": self.created_at.isoformat()
            if self.created_at is not None
            else None,
            "updated_at": self.updated_at.isoformat()
            if self.updated_at is not None
            else None,
        }

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> KnowledgeGraphEntityRecord:
        entity_val = row.get("entity")
        record_identifier_val = row.get("record_identifier")
        normalized_record_identifier_val = row.get("normalized_record_identifier")
        column_values_val = row.get("column_values")
        column_values = (
            column_values_val if isinstance(column_values_val, dict) else None
        )
        identifier_aliases_val = row.get("identifier_aliases")

        identifier_aliases = (
            [str(v) for v in identifier_aliases_val if v is not None]
            if isinstance(identifier_aliases_val, list)
            else None
        )

        return cls(
            id=to_uuid(row.get("id")),
            entity=str(entity_val) if entity_val is not None else "",
            record_identifier=str(record_identifier_val)
            if record_identifier_val is not None
            else "",
            normalized_record_identifier=str(normalized_record_identifier_val)
            if normalized_record_identifier_val is not None
            else "",
            column_values=column_values,
            identifier_aliases=identifier_aliases,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


def knowledge_graph_entity_table(metadata: MetaData, table_name: str) -> Table:
    """Internal SQLAlchemy Core `Table` builder for per-graph entities tables."""

    return Table(
        table_name,
        metadata,
        Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        Column("entity", String(255), nullable=False),
        Column("record_identifier", String(500), nullable=False),
        Column("normalized_record_identifier", String(500), nullable=False),
        Column(
            "column_values",
            JSONB,
            nullable=False,
            server_default=text("'{}'::jsonb"),
        ),
        Column(
            "identifier_aliases",
            JSONB,
            nullable=False,
            server_default=text("'[]'::jsonb"),
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
