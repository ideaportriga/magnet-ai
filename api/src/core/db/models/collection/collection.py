from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class Collection(UUIDAuditSimpleBase):
    """Main API tools table using base entity class with variant validation."""

    __tablename__ = "collections"

    # API configuration fields
    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Collection type (e.g., 'documents', 'images')",
    )

    ai_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Model used for processing (e.g., 'AZURE_AI_TEXT-EMBEDDING-3-SMALL')",
    )

    source: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Source configuration for the collection"
    )

    chunking: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Chunking configuration for the collection"
    )

    indexing: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Indexing configuration for the collection"
    )

    last_synced: Mapped[Optional[datetime]] = mapped_column(
        DateTimeUTC, nullable=True, comment="Last synced timestamp for the collection"
    )

    job_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Job ID associated with the collection"
    )
