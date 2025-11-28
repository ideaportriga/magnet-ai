from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditEntityBase


class APITool(UUIDAuditEntityBase):
    """Main API tools table using base entity class with variant validation."""

    __tablename__ = "api_tools"

    # API configuration fields
    api_provider: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="API provider name"
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="API endpoint path"
    )
    method: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="HTTP method (GET, POST, etc.)"
    )

    # Complex nested objects stored as JSONB
    mock: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Mock data configuration"
    )
    original_parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Original API parameters schema"
    )
    original_operation_definition: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Original OpenAPI operation definition"
    )
