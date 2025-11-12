from __future__ import annotations

from ..base import UUIDAuditEntityBase


class RagTool(UUIDAuditEntityBase):
    """Main RAG tools table using base entity class with variant validation."""

    __tablename__ = "rag_tools"
