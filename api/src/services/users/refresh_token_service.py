"""
Refresh token service — create, rotate, revoke with family-based reuse detection.

Security model:
- Tokens are stored as SHA-256 hashes (never plaintext)
- Each login creates a new "family" (family_id)
- Token rotation: old token is revoked, new one created in same family
- Reuse detection: if a revoked token is presented, entire family is revoked
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError, OperationalError

from core.config.base import get_auth_settings
from core.db.models.user.refresh_token import RefreshToken
from core.exceptions import AuthError, ConflictError

_LOCK_NOT_AVAILABLE_PGCODE = "55P03"


def _is_lock_not_available(exc: BaseException) -> bool:
    """Return True if exc represents PostgreSQL row-lock contention from NOWAIT."""
    pgcode = getattr(getattr(exc, "orig", None), "pgcode", None)
    if pgcode == _LOCK_NOT_AVAILABLE_PGCODE:
        return True
    message = str(exc).lower()
    return "could not obtain lock" in message or "lock not available" in message


async def _has_active_token_in_family(session: Any, family_id: UUID) -> bool:
    """Return True if family still has at least one non-revoked, non-expired token.

    Used to distinguish a benign rotation race (active successor exists)
    from a cascaded family revoke after reuse detection (no successor).
    """
    now = datetime.now(UTC)
    stmt = (
        select(RefreshToken.id)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


logger = getLogger(__name__)


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_refresh_token(
    session: Any,
    user_id: UUID,
    device_info: str | None = None,
    family_id: UUID | None = None,
    client_id: str | None = None,
    audience: str | None = None,
) -> tuple[str, RefreshToken]:
    """Create a new refresh token and persist its hash.

    Args:
        session: SQLAlchemy async session.
        user_id: The user this token belongs to.
        device_info: Optional User-Agent string.
        family_id: If rotating, reuse the existing family. Otherwise new.
        client_id: OAuth client_id (e.g. "claude") when this session belongs
            to an OAuth/MCP flow. NULL for web-cookie sessions.
        audience: RFC 8707 resource URI carried by access tokens this family
            issues. NULL for legacy web-cookie sessions.

    Returns:
        Tuple of (plaintext_token, RefreshToken db object).
    """
    settings = get_auth_settings()
    plaintext = generate_refresh_token()
    token_hash = hash_token(plaintext)

    if family_id is None:
        family_id = uuid4()

    db_token = RefreshToken(
        token_hash=token_hash,
        family_id=family_id,
        user_id=user_id,
        device_info=device_info,
        expires_at=datetime.now(UTC)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS),
        client_id=client_id,
        audience=audience,
    )
    session.add(db_token)
    return plaintext, db_token


async def validate_and_rotate(
    session: Any,
    plaintext_token: str,
    device_info: str | None = None,
) -> tuple[str, RefreshToken, UUID]:
    """Validate an existing refresh token and rotate it.

    Implements family-based reuse detection:
    - If the token is already revoked → revoke entire family (theft detected)
    - If the token is expired → reject
    - If valid → revoke current, issue new in same family

    Args:
        session: SQLAlchemy async session.
        plaintext_token: The refresh token from the client cookie.
        device_info: Optional User-Agent for the new token.

    Returns:
        Tuple of (new_plaintext_token, new_RefreshToken, user_id).

    Raises:
        AuthError: If token is invalid, expired, or reuse detected.
    """
    token_hash = hash_token(plaintext_token)

    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update(nowait=True)
    )
    try:
        result = await session.execute(stmt)
    except (OperationalError, DBAPIError) as exc:
        if _is_lock_not_available(exc):
            raise ConflictError("Token validation in progress, please retry") from exc
        raise
    db_token = result.scalar_one_or_none()

    if db_token is None:
        raise AuthError("Invalid refresh token")

    now = datetime.now(UTC)

    # Reuse detection: token already revoked → compromise!
    if db_token.revoked_at is not None:
        settings = get_auth_settings()
        reuse_grace_seconds = settings.REFRESH_TOKEN_REUSE_GRACE_SECONDS
        within_grace_window = (
            reuse_grace_seconds > 0
            and (now - db_token.revoked_at).total_seconds() <= reuse_grace_seconds
        )
        # Only treat as benign rotation race if the family still has an
        # active successor token. A revoked token without an active sibling
        # means the family was revoked as a whole (logout / reuse cascade)
        # and must not be soft-failed.
        if within_grace_window and await _has_active_token_in_family(
            session, db_token.family_id
        ):
            logger.info(
                "Refresh token already rotated within grace window for family %s user %s",
                db_token.family_id,
                db_token.user_id,
            )
            raise ConflictError("Refresh token already rotated, please retry")

        logger.warning(
            "Refresh token reuse detected! Revoking entire family %s for user %s",
            db_token.family_id,
            db_token.user_id,
        )
        await _revoke_family(session, db_token.family_id)
        raise AuthError("Refresh token reuse detected — all sessions revoked")

    # Expired
    if db_token.expires_at < now:
        raise AuthError("Refresh token expired")

    # Revoke current token
    db_token.revoked_at = now

    # Create new token in the same family — preserve client_id + audience so
    # MCP/OAuth flows keep their audience binding across rotations.
    new_plaintext, new_db_token = await create_refresh_token(
        session=session,
        user_id=db_token.user_id,
        device_info=device_info,
        family_id=db_token.family_id,
        client_id=db_token.client_id,
        audience=db_token.audience,
    )

    return new_plaintext, new_db_token, db_token.user_id


async def revoke_token_family(session: Any, token_hash: str) -> None:
    """Revoke all tokens in the same family as the given token (for logout)."""
    stmt = select(RefreshToken.family_id).where(RefreshToken.token_hash == token_hash)
    result = await session.execute(stmt)
    family_id = result.scalar_one_or_none()
    if family_id:
        await _revoke_family(session, family_id)


async def revoke_all_user_sessions(
    session: Any,
    user_id: UUID,
    except_token_hash: str | None = None,
) -> int:
    """Revoke all active refresh tokens for a user.

    Args:
        session: SQLAlchemy async session.
        user_id: The user whose sessions to revoke.
        except_token_hash: If provided, keep this token's family active.

    Returns:
        Number of tokens revoked.
    """
    now = datetime.now(UTC)
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    if except_token_hash:
        # Find the family of the current token to keep it
        fam_stmt = select(RefreshToken.family_id).where(
            RefreshToken.token_hash == except_token_hash
        )
        fam_result = await session.execute(fam_stmt)
        keep_family = fam_result.scalar_one_or_none()
        if keep_family:
            stmt = stmt.where(RefreshToken.family_id != keep_family)

    result = await session.execute(stmt)
    return result.rowcount


async def get_active_sessions(session: Any, user_id: UUID) -> list[RefreshToken]:
    """List active (non-revoked, non-expired) refresh tokens for a user."""
    now = datetime.now(UTC)
    stmt = (
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def revoke_session_by_id(session: Any, token_id: UUID, user_id: UUID) -> bool:
    """Revoke a specific session (entire family) by token ID."""
    stmt = select(RefreshToken).where(
        RefreshToken.id == token_id,
        RefreshToken.user_id == user_id,
    )
    result = await session.execute(stmt)
    db_token = result.scalar_one_or_none()
    if not db_token:
        return False
    await _revoke_family(session, db_token.family_id)
    return True


async def cleanup_expired_tokens() -> int:
    """Remove expired and revoked refresh tokens older than 30 days.

    Intended to be called periodically by the scheduler to prevent
    unbounded growth of the refresh_tokens table.

    Returns:
        Number of rows deleted.
    """
    from core.config.app import alchemy

    cutoff = datetime.now(UTC) - timedelta(days=30)

    async with alchemy.get_session() as session:
        from sqlalchemy import delete

        stmt = delete(RefreshToken).where(
            (RefreshToken.expires_at < cutoff)
            | (
                RefreshToken.revoked_at.is_not(None)
                & (RefreshToken.revoked_at < cutoff)
            )
        )
        result = await session.execute(stmt)
        await session.commit()
        deleted = result.rowcount
        if deleted:
            logger.info("Cleaned up %d expired/revoked refresh tokens", deleted)
        return deleted


async def _revoke_family(session: Any, family_id: UUID) -> None:
    """Revoke all tokens in a family."""
    now = datetime.now(UTC)
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await session.execute(stmt)
