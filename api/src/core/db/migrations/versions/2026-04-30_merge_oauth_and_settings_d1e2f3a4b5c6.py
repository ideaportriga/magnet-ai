# type: ignore
"""Merge oauth_client (c0d1e2f3a4b5) and add_settings_revision (c20acfe0b890) heads.

Background: the alpha branch was rewritten and the original `feat(mcp)` commit
that introduced revision `c0d1e2f3a4b5` (oauth_client + oauth_authorization_code
tables) was discarded. The migration file was restored on its own so alembic can
match the revision already recorded in the deployed DB, but it now coexists with
the `c20acfe0b890` head from the squashed migration work — leaving the tree with
two heads.

This is a no-op merge: it joins both branches so `alembic upgrade head` resolves
to a single revision again. The deployed DB sitting at `c0d1e2f3a4b5` will, on
next upgrade, replay the missing taskiq (a2b3c4d5e6f7) and settings_revision
(c20acfe0b890) migrations from the other branch and then advance to this merge.

Revision ID: d1e2f3a4b5c6
Revises: ('c0d1e2f3a4b5', 'c20acfe0b890')
Create Date: 2026-04-30 00:00:00.000000+00:00
"""

from __future__ import annotations

revision = "d1e2f3a4b5c6"
down_revision = ("c0d1e2f3a4b5", "c20acfe0b890")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op — pure merge of two heads."""


def downgrade() -> None:
    """No-op — splitting back into two heads is reversible by removing this file."""
