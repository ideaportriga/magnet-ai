# type: ignore
"""add_mcp_server_security_configuration

Revision ID: 544aba6a557c
Revises: c7e9a1b3d5f4
Create Date: 2026-09-23 09:17:37.540923+00:00

"""

from __future__ import annotations

import warnings

import advanced_alchemy.types.json
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]


revision = "544aba6a557c"
down_revision = "c7e9a1b3d5f4"
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
    """Add MCP server security configuration columns."""
    op.add_column(
        "mcp_servers",
        sa.Column(
            "security_scheme",
            sa.JSON()
            .with_variant(
                postgresql.JSONB(astext_type=sa.Text),
                "cockroachdb",
            )
            .with_variant(
                advanced_alchemy.types.json.ORA_JSONB(),
                "oracle",
            )
            .with_variant(
                postgresql.JSONB(astext_type=sa.Text),
                "postgresql",
            ),
            nullable=True,
            comment="Security scheme configuration",
        ),
    )

    op.add_column(
        "mcp_servers",
        sa.Column(
            "security_values",
            sa.JSON()
            .with_variant(
                postgresql.JSONB(astext_type=sa.Text),
                "cockroachdb",
            )
            .with_variant(
                advanced_alchemy.types.json.ORA_JSONB(),
                "oracle",
            )
            .with_variant(
                postgresql.JSONB(astext_type=sa.Text),
                "postgresql",
            ),
            nullable=True,
            comment="Security values configuration",
        ),
    )

    op.add_column(
        "mcp_servers",
        sa.Column(
            "last_synced_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
            comment="Last tool synchronization timestamp",
        ),
    )


def schema_downgrades() -> None:
    """Remove MCP server security configuration columns."""
    op.drop_column("mcp_servers", "security_values")
    op.drop_column("mcp_servers", "security_scheme")
    op.drop_column("mcp_servers", "last_synced_at")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here."""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here."""
