from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy.orm import Mapped, mapped_column

from core.db.models.base import UUIDAuditSimpleBase


class Settings(UUIDAuditSimpleBase):
    __tablename__ = "settings"

    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Settings in JSON format",
    )
