"""
Provider table definition for storing external connection configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config.base import get_general_settings
from core.db.types import EncryptedJsonB

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..ai_model import AIModel
    from ..collection import Collection


class Provider(UUIDAuditSimpleBase):
    """
    Provider entity for storing external connection configurations.

    This model stores connection information for various external providers
    like LLM providers, embedding providers, and data sources.
    
    Inherited fields from UUIDAuditSimpleBase:
    - id, created_at, updated_at (from UUIDv7AuditBase)
    - name: provider name
    - description: provider description
    - system_name: provider identifier (e.g., 'azure_open_ai', 'openai', 'oci')
    - category: provider type (e.g., 'llm', 'embedding', 'data_source')
    - created_by, updated_by: user tracking
    
    Credentials and sensitive data are encrypted using EncryptedJsonB.
    """

    __tablename__ = "providers"

    # Provider type field
    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Provider type (e.g., 'openai', 'azure', 'anthropic')",
        index=True,
    )

    # Connection configuration (non-sensitive)
    connection_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Provider configuration (non-sensitive settings)",
    )

    # Encrypted credentials and sensitive data
    secrets_encrypted: Mapped[Optional[dict[str, Any]]] = mapped_column(
        EncryptedJsonB(key=get_general_settings().SECRET_ENCRYPTION_KEY),
        nullable=True,
        comment="Encrypted credentials and sensitive connection data",
    )

    # Additional metadata
    metadata_info: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Additional metadata about the provider",
    )

    # Relationships with child entities
    ai_models: Mapped[list["AIModel"]] = relationship(
        "AIModel",
        back_populates="provider_rel",
        foreign_keys="AIModel.provider_system_name",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    collections: Mapped[list["Collection"]] = relationship(
        "Collection",
        back_populates="provider_rel",
        foreign_keys="Collection.provider_system_name",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Provider(system_name='{self.system_name}', category='{self.category}')>"
