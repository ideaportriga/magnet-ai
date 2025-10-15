# type: ignore
"""migrate_provider_name_to_provider_system_name

Revision ID: b8e8a481b4f7
Revises: b1fe5f31929b
Create Date: 2025-10-09 06:18:02.420207+00:00

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC
from sqlalchemy import Text  # noqa: F401
import advanced_alchemy.types
import advanced_alchemy.types.datetime
import advanced_alchemy.types.json
if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
# Additional type aliases for proper migration generation
sa.Text = Text


# revision identifiers, used by Alembic.
revision = 'b8e8a481b4f7'
down_revision = 'b1fe5f31929b'
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
    # No schema changes needed for this migration

def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    # No schema changes to revert

def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""
    # Migrate data from provider_name to provider_system_name in ai_models table
    # Convert provider_name to UPPER_CASE and set it as provider_system_name
    
    connection = op.get_bind()
    
    # Step 1: Get all unique provider_name values from ai_models
    result = connection.execute(
        sa.text("""
            SELECT DISTINCT provider_name 
            FROM ai_models 
            WHERE provider_name IS NOT NULL
        """)
    )
    unique_providers = [row[0] for row in result]
    
    # Step 2: Create provider records for each unique provider_name if they don't exist
    from datetime import datetime, timezone
    import uuid
    
    for provider_name in unique_providers:
        system_name_upper = provider_name.upper()
        
        # Check if provider already exists
        existing = connection.execute(
            sa.text("""
                SELECT COUNT(*) 
                FROM providers 
                WHERE system_name = :system_name
            """),
            {"system_name": system_name_upper}
        ).scalar()
        
        if existing == 0:
            # Create new provider record
            now = datetime.now(timezone.utc)
            provider_id = uuid.uuid4()
            
            connection.execute(
                sa.text("""
                    INSERT INTO providers (
                        id, 
                        name, 
                        system_name, 
                        type,
                        description,
                        created_at, 
                        updated_at
                    ) VALUES (
                        :id,
                        :name,
                        :system_name,
                        :type,
                        :description,
                        :created_at,
                        :updated_at
                    )
                """),
                {
                    "id": str(provider_id),
                    "name": provider_name,
                    "system_name": system_name_upper,
                    "type": provider_name,
                    "description": f"Auto-generated provider for {provider_name}",
                    "created_at": now,
                    "updated_at": now
                }
            )
            print(f"✅ Created provider record: {system_name_upper} (type: {provider_name})")
    
    # Step 3: Update ai_models table: copy provider_name to provider_system_name in UPPER_CASE
    connection.execute(
        sa.text("""
            UPDATE ai_models 
            SET provider_system_name = UPPER(provider_name)
            WHERE provider_system_name IS NULL OR provider_system_name = ''
        """)
    )
    
    print("✅ Successfully migrated provider_name to provider_system_name (UPPER_CASE) in ai_models table")

def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
    # Revert the migration by clearing provider_system_name values
    
    connection = op.get_bind()
    
    # Step 1: Get all provider system_names that were auto-generated
    result = connection.execute(
        sa.text("""
            SELECT DISTINCT system_name 
            FROM providers 
            WHERE description LIKE 'Auto-generated provider for%'
        """)
    )
    auto_generated_providers = [row[0] for row in result]
    
    # Step 2: Clear provider_system_name in ai_models table
    connection.execute(
        sa.text("""
            UPDATE ai_models 
            SET provider_system_name = NULL
            WHERE provider_system_name IS NOT NULL
        """)
    )
    
    # Step 3: Delete auto-generated provider records
    for system_name in auto_generated_providers:
        connection.execute(
            sa.text("""
                DELETE FROM providers 
                WHERE system_name = :system_name 
                AND description LIKE 'Auto-generated provider for%'
            """),
            {"system_name": system_name}
        )
        print(f"✅ Deleted auto-generated provider: {system_name}")
    
    print("✅ Successfully cleared provider_system_name values in ai_models table")
