from __future__ import annotations

from ..base import UUIDAuditEntityBase


class RetrievalTool(UUIDAuditEntityBase):
    """Main Retrieval tools table using base entity class with variant validation."""

    __tablename__ = "retrieval_tools"
