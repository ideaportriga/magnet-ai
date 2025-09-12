from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class AIApp(UUIDAuditSimpleBase):
    """Main AI app table using base entity class with variant validation."""

    __tablename__ = "ai_apps"

    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="AI app settings"
    )

    tabs: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True, comment="Tabs configuration"
    )
