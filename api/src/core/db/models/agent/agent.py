from __future__ import annotations

from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditEntityBase


class Agent(UUIDAuditEntityBase):
    """Main AI app table using base entity class with variant validation."""
    channels: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, comment="List of agent channels")
    __tablename__ = "agents"
