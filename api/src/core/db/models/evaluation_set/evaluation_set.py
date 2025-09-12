from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class EvaluationSet(UUIDAuditSimpleBase):
    """Main evaluation sets table using base entity class with variant validation."""

    __tablename__ = "evaluation_sets"
    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of evaluation set (e.g., 'test', 'validation')",
    )
    items: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True, comment="List of items in the evaluation set"
    )
