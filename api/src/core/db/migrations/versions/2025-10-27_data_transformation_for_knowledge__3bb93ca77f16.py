# type: ignore
"""Data transformation for knowledge sources

Revision ID: 3bb93ca77f16
Revises: f82c14db4dfc
Create Date: 2025-10-27 14:15:38.309165+00:00

"""
from __future__ import annotations

import warnings
import uuid

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC
from sqlalchemy import Text  # noqa: F401

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
# Additional type aliases for proper migration generation
sa.Text = Text


# revision identifiers, used by Alembic.
revision = '3bb93ca77f16'
down_revision = 'f9d9c0b1d4b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()

def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()

def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    # No schema changes needed

def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    # No schema changes to downgrade

def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""
    # Define knowledge source types and their human-readable names
    knowledge_source_types = [
        ('Oracle Knowledge', 'Oracle Knowledge'),
        ('Salesforce', 'Salesforce'),
        ('Sharepoint', 'Sharepoint'),
        ('Confluence', 'Confluence'),
        ('Hubspot', 'Hubspot'),
        ('RightNow', 'RightNow'),
        ('Fluid Topics', 'Fluid Topics'),
        ('File', 'File'),
        ('Documentation', 'Documentation'),
        ('Sharepoint Pages', 'Sharepoint Pages'),
    ]
    
    connection = op.get_bind()
    
    # Create providers for each knowledge source type
    for source_type, name in knowledge_source_types:
        provider_id = str(uuid.uuid4())
        connection.execute(
            sa.text("""
                INSERT INTO providers (id, type, name, system_name, category, created_at, updated_at)
                VALUES (:id, :type, :name, :system_name, 'knowledge', NOW(), NOW())
                ON CONFLICT (system_name) DO NOTHING
            """),
            {
                "id": provider_id,
                "type": source_type,
                "name": name,
                "system_name": source_type
            }
        )
    
    # Update collections to set provider_system_name based on source_type
    for source_type, _ in knowledge_source_types:
        connection.execute(
            sa.text("""
                UPDATE collections 
                SET provider_system_name = :system_name
                WHERE provider_system_name IS NULL 
                AND source->>'source_type' = :source_type
            """),
            {"system_name": source_type, "source_type": source_type}
        )

def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
