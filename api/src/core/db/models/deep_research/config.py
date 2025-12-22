"""Deep Research Config database model."""

from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class DeepResearchConfig(UUIDAuditSimpleBase):
    __tablename__ = "deep_research_configs"

    # Configuration stored as flexible JSONB for future adjustments
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Deep research configuration in JSON format"
    )
