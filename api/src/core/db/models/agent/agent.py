from __future__ import annotations

from ..base import UUIDAuditEntityBase


class Agent(UUIDAuditEntityBase):
    """Main AI app table using base entity class with variant validation."""

    __tablename__ = "agents"
