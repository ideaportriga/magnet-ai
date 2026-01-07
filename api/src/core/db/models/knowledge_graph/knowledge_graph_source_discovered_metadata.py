from __future__ import annotations

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import GUID
from sqlalchemy import Column, ForeignKey, Table

# Association table between knowledge graph sources and discovered metadata fields.
# This enables per-source attribution of discovered metadata.
knowledge_graph_source_discovered_metadata_table = Table(
    "knowledge_graph_sources_discovered_metadata",
    UUIDv7AuditBase.metadata,
    Column(
        "source_id",
        GUID(),
        ForeignKey("knowledge_graph_sources.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "discovered_metadata_id",
        GUID(),
        ForeignKey("knowledge_graph_discovered_metadata.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)
