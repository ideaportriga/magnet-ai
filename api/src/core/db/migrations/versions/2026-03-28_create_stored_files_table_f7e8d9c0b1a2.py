# type: ignore
"""Create stored_files table for unified file storage.

Revision ID: a1b2c3d4e5f6
Revises: 5d27c945385a
Create Date: 2026-03-28 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
]


# revision identifiers, used by Alembic.
revision = "f7e8d9c0b1a2"
down_revision = "5d27c945385a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_downgrades()


def schema_upgrades() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS stored_files (
            id UUID NOT NULL,
            backend_key VARCHAR(50) NOT NULL,
            path VARCHAR(1024) NOT NULL,
            filename VARCHAR(512) NOT NULL,
            content_type VARCHAR(255) NOT NULL,
            size BIGINT NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id UUID NOT NULL,
            deleted_at TIMESTAMP WITH TIME ZONE,
            extra JSONB,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_stored_files PRIMARY KEY (id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_stored_files_entity
        ON stored_files (entity_type, entity_id)
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_stored_files_backend_path
        ON stored_files (backend_key, path)
    """)


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_stored_files_backend_path")
    op.execute("DROP INDEX IF EXISTS ix_stored_files_entity")
    op.execute("DROP TABLE IF EXISTS stored_files")
