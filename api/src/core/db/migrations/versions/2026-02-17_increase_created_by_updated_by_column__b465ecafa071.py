# type: ignore
"""increase created_by updated_by column length to 255

Revision ID: b465ecafa071
Revises: 002e7d0ff790
Create Date: 2026-02-17 13:36:57.830513+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import (
    EncryptedString,
    EncryptedText,
    GUID,
    ORA_JSONB,
    DateTimeUTC,
)
from sqlalchemy import Text  # noqa: F401

if TYPE_CHECKING:
    pass

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
# Additional type aliases for proper migration generation
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "b465ecafa071"
down_revision = "002e7d0ff790"
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
    op.alter_column(
        "agents",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "agents",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_apps",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_apps",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_models",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_models",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_servers",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_servers",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_tools",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_tools",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "collections",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "collections",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "deep_research_configs",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "deep_research_configs",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "evaluation_sets",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "evaluation_sets",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "knowledge_graphs",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "knowledge_graphs",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "mcp_servers",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "mcp_servers",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "note_taker_settings",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "note_taker_settings",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "prompts",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "prompts",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "providers",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "providers",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "rag_tools",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "rag_tools",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "retrieval_tools",
        "created_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who created the entity",
        existing_comment="ID of the user who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "retrieval_tools",
        "updated_by",
        existing_type=sa.VARCHAR(length=36),
        type_=sa.String(length=255),
        comment="User who last updated the entity",
        existing_comment="ID of the user who last updated the entity",
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "retrieval_tools",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "retrieval_tools",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "rag_tools",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "rag_tools",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "providers",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "providers",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "prompts",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "prompts",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "note_taker_settings",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "note_taker_settings",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "mcp_servers",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "mcp_servers",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "knowledge_graphs",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "knowledge_graphs",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "evaluation_sets",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "evaluation_sets",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "deep_research_configs",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "deep_research_configs",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "collections",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "collections",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_tools",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_tools",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_servers",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "api_servers",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_models",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_models",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_apps",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "ai_apps",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "agents",
        "updated_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who last updated the entity",
        existing_comment="User who last updated the entity",
        existing_nullable=True,
    )
    op.alter_column(
        "agents",
        "created_by",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=36),
        comment="ID of the user who created the entity",
        existing_comment="User who created the entity",
        existing_nullable=True,
    )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
