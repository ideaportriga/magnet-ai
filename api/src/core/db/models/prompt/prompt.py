from __future__ import annotations

from ..base import UUIDAuditEntityBase


class Prompt(UUIDAuditEntityBase):
    """Main prompts table using base entity class with variant validation."""

    __tablename__ = "prompts"
