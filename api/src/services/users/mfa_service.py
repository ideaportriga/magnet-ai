"""
MFA (Multi-Factor Authentication) service — TOTP setup, verification, backup codes.

Uses pyotp for TOTP (RFC 6238) and qrcode for QR code generation.
Backup codes are hashed with Argon2 (same as passwords).
"""

from __future__ import annotations

import base64
import io
import secrets
from datetime import UTC, datetime
from logging import getLogger
from typing import Any

import pyotp
import qrcode

from core.db.models.user.user import User
from core.exceptions import AuthError
from services.users.password import hash_password, verify_password

logger = getLogger(__name__)

# Number of backup codes to generate
BACKUP_CODES_COUNT = 8
# Length of each backup code (hex chars)
BACKUP_CODE_LENGTH = 8
# App name shown in authenticator apps
TOTP_ISSUER = "Magnet AI"


def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32 encoded)."""
    return pyotp.random_base32()


def generate_provisioning_uri(secret: str, email: str) -> str:
    """Generate a provisioning URI for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=TOTP_ISSUER)


def generate_qr_code_base64(provisioning_uri: str) -> str:
    """Generate a QR code as base64-encoded PNG."""
    img = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code (with 30-second window tolerance)."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_backup_codes() -> list[str]:
    """Generate a set of plaintext backup codes."""
    return [
        secrets.token_hex(BACKUP_CODE_LENGTH // 2) for _ in range(BACKUP_CODES_COUNT)
    ]


def hash_backup_codes(codes: list[str]) -> list[str]:
    """Hash backup codes for storage (Argon2)."""
    return [hash_password(code) for code in codes]


async def setup_mfa(user: User) -> dict:
    """Begin MFA setup — generate secret and QR code.

    The secret is NOT saved to DB yet. It's returned to the user
    who must confirm by providing a valid TOTP code.

    Returns:
        Dict with secret, qr_code (base64 PNG), provisioning_uri.
    """
    secret = generate_totp_secret()
    uri = generate_provisioning_uri(secret, user.email)
    qr_base64 = generate_qr_code_base64(uri)

    return {
        "secret": secret,
        "provisioning_uri": uri,
        "qr_code": qr_base64,
    }


async def confirm_mfa_setup(
    session: Any,
    user: User,
    secret: str,
    totp_code: str,
) -> list[str]:
    """Confirm MFA setup by verifying a TOTP code, then save secret + backup codes.

    Args:
        session: SQLAlchemy async session.
        user: The user enabling MFA.
        secret: The TOTP secret from setup step.
        totp_code: 6-digit code from authenticator app.

    Returns:
        List of plaintext backup codes (shown once, never retrievable).

    Raises:
        AuthError: If TOTP code is invalid.
    """
    if not verify_totp_code(secret, totp_code):
        raise AuthError("Invalid TOTP code")

    # Generate and hash backup codes
    plaintext_codes = generate_backup_codes()
    hashed_codes = hash_backup_codes(plaintext_codes)

    # Save to user
    user.totp_secret = secret
    user.backup_codes = hashed_codes
    user.is_two_factor_enabled = True
    user.two_factor_confirmed_at = datetime.now(UTC)

    return plaintext_codes


async def verify_mfa(
    session: Any,
    user: User,
    code: str,
) -> bool:
    """Verify a MFA code (TOTP or backup code).

    If a backup code is used, it's consumed (set to None in the list).

    Args:
        session: SQLAlchemy async session.
        user: The user to verify.
        code: 6-digit TOTP code or 8-char backup code.

    Returns:
        True if verification succeeded.
    """
    # Load deferred fields
    await session.refresh(user, attribute_names=["totp_secret", "backup_codes"])

    if not user.totp_secret:
        return False

    # Try TOTP first (6-digit code)
    if len(code) == 6 and code.isdigit():
        if verify_totp_code(user.totp_secret, code):
            return True

    # Try backup codes
    if user.backup_codes:
        for i, hashed_code in enumerate(user.backup_codes):
            if hashed_code is not None and verify_password(code, hashed_code):
                # Consume the backup code
                user.backup_codes[i] = None
                # Force SQLAlchemy to detect the change (JSONB mutation)
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(user, "backup_codes")
                logger.info("Backup code used by user %s (index %d)", user.email, i)
                return True

    return False


async def disable_mfa(
    session: Any,
    user: User,
) -> None:
    """Disable MFA for a user."""
    user.totp_secret = None
    user.backup_codes = None
    user.is_two_factor_enabled = False
    user.two_factor_confirmed_at = None
