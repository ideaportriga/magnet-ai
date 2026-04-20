# type: ignore
"""Encrypt totp_secret column — change type to TEXT for EncryptedText.

Existing plaintext TOTP secrets are re-encrypted using Fernet (SECRET_ENCRYPTION_KEY).
The column type changes from VARCHAR(255) to TEXT to accommodate encrypted values.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-07 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
]

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
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
            schema_downgrades()


def schema_upgrades() -> None:
    # Change column type from VARCHAR(255) to TEXT to accommodate encrypted values.
    # EncryptedText (Fernet) produces output longer than 255 chars for typical
    # base32 TOTP secrets (32 chars plaintext → ~120+ chars encrypted).
    op.execute("""
        ALTER TABLE user_account
        ALTER COLUMN totp_secret TYPE TEXT
    """)


def data_upgrades() -> None:
    """Re-encrypt existing plaintext TOTP secrets.

    This uses pgcrypto for a server-side approach, but since Fernet
    encryption requires the app-layer key, we handle it in Python.
    Existing rows with non-NULL totp_secret need to be re-encrypted.

    NOTE: This migration must be run while the application has
    SECRET_ENCRYPTION_KEY configured. If there are existing TOTP secrets
    they will be encrypted in-place using the app's Fernet key.
    """
    import os

    encryption_key = os.environ.get("SECRET_ENCRYPTION_KEY", "")
    if not encryption_key:
        # No encryption key — skip data migration.
        # Secrets will be encrypted on next MFA setup/confirm.
        import logging

        logging.getLogger(__name__).warning(
            "SECRET_ENCRYPTION_KEY not set — skipping TOTP secret encryption. "
            "Existing plaintext secrets will remain until next MFA confirm."
        )
        return

    # Use raw connection to read and update secrets
    from alembic import op as _op

    connection = _op.get_bind()

    from cryptography.fernet import Fernet, InvalidToken

    # Guard against invalid Fernet key (dev installs often carry a legacy
    # shipped default that isn't 32 url-safe base64-encoded bytes). Treat
    # it the same as "no key" — skip data migration, schema change still
    # applies; any plaintext secrets will be encrypted on next MFA setup.
    try:
        fernet = Fernet(
            encryption_key.encode("utf-8")
            if isinstance(encryption_key, str)
            else encryption_key
        )
    except (ValueError, Exception) as e:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning(
            "SECRET_ENCRYPTION_KEY is not a valid Fernet key (%s) — skipping "
            "TOTP secret encryption data migration. Schema change still applies.",
            e,
        )
        return

    from sqlalchemy import text

    # Read all rows with non-null totp_secret
    result = connection.execute(
        text("SELECT id, totp_secret FROM user_account WHERE totp_secret IS NOT NULL")
    )

    rows = result.fetchall()
    if not rows:
        return

    import logging

    logger = logging.getLogger(__name__)
    encrypted_count = 0
    skipped_count = 0

    for row in rows:
        user_id, secret = row[0], row[1]

        # Check if already encrypted (Fernet tokens start with 'gAAAAA')
        if secret and secret.startswith("gAAAAA"):
            # Already looks encrypted — verify
            try:
                fernet.decrypt(secret.encode("utf-8"))
                skipped_count += 1
                continue  # Already encrypted, skip
            except (InvalidToken, Exception):
                pass  # Not valid Fernet — encrypt it

        if secret:
            encrypted = fernet.encrypt(secret.encode("utf-8")).decode("utf-8")
            connection.execute(
                text("UPDATE user_account SET totp_secret = :secret WHERE id = :id"),
                {"secret": encrypted, "id": user_id},
            )
            encrypted_count += 1

    logger.info(
        "TOTP secret migration: encrypted=%d, already_encrypted=%d",
        encrypted_count,
        skipped_count,
    )


def schema_downgrades() -> None:
    # Revert column type. WARNING: This will truncate encrypted values
    # that exceed 255 chars. Data loss is expected on downgrade.
    op.execute("""
        ALTER TABLE user_account
        ALTER COLUMN totp_secret TYPE VARCHAR(255)
    """)
