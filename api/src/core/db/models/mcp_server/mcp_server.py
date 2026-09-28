from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.config.base import get_general_settings
from core.db.types import EncryptedJsonB

from ..base import UUIDAuditSimpleBase


class MCPServer(UUIDAuditSimpleBase):
    """Main MCP server table using base entity class with variant validation."""

    __tablename__ = "mcp_servers"

    transport: Mapped[str] = mapped_column(
        String, nullable=False, comment="Transport protocol (e.g., sse)"
    )
    url: Mapped[str] = mapped_column(String, nullable=False, comment="MCP server URL")
    headers: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="HTTP headers configuration"
    )
    security_scheme: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Security scheme configuration"
    )
    security_values: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Security values configuration"
    )
    last_synced_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC, nullable=True, comment="Last tool synchronization timestamp"
    )
    tools: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True, comment="Tools configuration"
    )
    secrets_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(
        EncryptedJsonB(key=get_general_settings().SECRET_ENCRYPTION_KEY)
    )
