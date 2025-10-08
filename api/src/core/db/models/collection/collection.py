from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..provider import Provider


class Collection(UUIDAuditSimpleBase):
    """Main API tools table using base entity class with variant validation."""

    __tablename__ = "collections"

    # Foreign key to Provider by system_name
    provider_system_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("providers.system_name", ondelete="CASCADE"),
        nullable=True,
        comment="Foreign key to provider system_name",
        index=True,
    )

    # Relationship to Provider (named provider_rel to avoid potential conflicts)
    provider_rel: Mapped[Optional["Provider"]] = relationship(
        "Provider",
        back_populates="collections",
        foreign_keys=[provider_system_name],
    )

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
