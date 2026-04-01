"""
User application service — handles user upsert from OIDC tokens and API keys.

This is the application-layer service that uses the domain-layer UsersService
for database operations. It contains business logic for syncing external
identity provider data with the internal User table.
"""

from __future__ import annotations

from datetime import UTC, datetime
from logging import getLogger
from typing import Any
from uuid import UUID

from core.config.app import alchemy
from core.db.models.user.role import Role
from core.db.models.user.user import User
from core.db.models.user.user_oauth_account import UserOAuthAccount
from core.db.models.user.user_role import UserRole
from core.domain.users.service import UsersService
from guards.role import DEFAULT_ROLE_SLUG

logger = getLogger(__name__)


async def upsert_user_from_oidc(
    auth_data: dict[str, Any],
    oauth_name: str,
    account_id: str,
) -> User:
    """Find or create a User from OIDC token data.

    On first login: creates User + UserOAuthAccount.
    On subsequent logins: updates last_login_at and syncs name/email from token.

    Args:
        auth_data: Decoded token data dict with keys: user_id, email, name, preferred_username.
        oauth_name: OAuth provider name ("microsoft" or "oracle").
        account_id: Unique user ID from the OAuth provider (oid/sub claim).

    Returns:
        The User instance (created or updated).
    """
    email = auth_data.get("email") or auth_data.get("preferred_username")
    if not email:
        logger.warning(
            "OIDC token missing email/preferred_username — cannot upsert user"
        )
        raise ValueError("OIDC token must contain email or preferred_username")

    name = auth_data.get("name")
    now = datetime.now(UTC)

    async with alchemy.get_session() as session:
        service = UsersService(session=session)

        # Try to find existing user by email
        user = await service.get_one_or_none(email=email)

        if user is None:
            # First login — create user
            user = await service.create(
                User(
                    email=email,
                    name=name,
                    is_active=True,
                    is_verified=True,  # OIDC users are pre-verified by the IdP
                    last_login_at=now,
                ),
                auto_commit=False,
            )
            # Assign default role
            await _assign_default_role(session, user.id)
            logger.info("Created new user from OIDC: %s", email)
        else:
            # Returning user — update last_login_at and sync name if changed
            user.last_login_at = now
            if name and user.name != name:
                user.name = name
            await service.update(user, auto_commit=False)

        # Sync roles from OIDC token → DB
        # IdP is the source of truth for OIDC users: roles added/removed in Entra ID
        # are reflected in DB on every login.
        oidc_roles = auth_data.get("roles", set())
        if isinstance(oidc_roles, list):
            oidc_roles = set(oidc_roles)
        await _sync_oidc_roles(session, user.id, oidc_roles)

        # Upsert OAuth account link
        await _upsert_oauth_account(
            session=session,
            user_id=user.id,
            oauth_name=oauth_name,
            account_id=account_id,
            account_email=email,
            now=now,
        )

        await session.commit()

        # Reload user with fresh roles (selectin)
        user = await service.get_one_or_none(email=email)
        return user


async def _upsert_oauth_account(
    session: Any,
    user_id: UUID,
    oauth_name: str,
    account_id: str,
    account_email: str | None,
    now: datetime,
) -> None:
    """Create or update UserOAuthAccount for this provider+account_id pair."""
    from sqlalchemy import select

    stmt = select(UserOAuthAccount).where(
        UserOAuthAccount.oauth_name == oauth_name,
        UserOAuthAccount.account_id == account_id,
    )
    result = await session.execute(stmt)
    oauth_account = result.scalar_one_or_none()

    if oauth_account is None:
        oauth_account = UserOAuthAccount(
            user_id=user_id,
            oauth_name=oauth_name,
            account_id=account_id,
            account_email=account_email,
            last_login_at=now,
        )
        session.add(oauth_account)
        logger.info(
            "Linked OAuth account %s/%s to user %s", oauth_name, account_id, user_id
        )
    else:
        oauth_account.last_login_at = now
        if account_email and oauth_account.account_email != account_email:
            oauth_account.account_email = account_email


async def _sync_oidc_roles(
    session: Any, user_id: UUID, oidc_role_slugs: set[str]
) -> None:
    """Sync user roles in DB to match OIDC token claims.

    - Roles present in OIDC but missing in DB → add
    - Roles present in DB but missing in OIDC → remove
    - Always ensure at least the default role is present

    This makes IdP the authoritative source for OIDC users.
    """
    from sqlalchemy import delete, select

    if not oidc_role_slugs:
        # Token has no roles claim — keep existing DB roles, just ensure default
        await _assign_default_role(session, user_id)
        return

    # Also include default role
    oidc_role_slugs = oidc_role_slugs | {DEFAULT_ROLE_SLUG}

    # Get all known roles from DB matching the OIDC slugs
    stmt = select(Role).where(Role.slug.in_(oidc_role_slugs))
    result = await session.execute(stmt)
    target_roles = {r.slug: r.id for r in result.scalars().all()}

    # Get current DB roles for this user
    stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
    result = await session.execute(stmt)
    current_role_ids = {r[0] for r in result.fetchall()}

    target_role_ids = set(target_roles.values())

    # Add missing roles
    to_add = target_role_ids - current_role_ids
    for role_id in to_add:
        session.add(UserRole(user_id=user_id, role_id=role_id))

    # Remove roles not in OIDC claims
    to_remove = current_role_ids - target_role_ids
    if to_remove:
        stmt = delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id.in_(to_remove),
        )
        await session.execute(stmt)

    if to_add or to_remove:
        added = [s for s, rid in target_roles.items() if rid in to_add]
        logger.info(
            "Synced OIDC roles for user %s: added=%s, removed=%d",
            user_id,
            added,
            len(to_remove),
        )


async def _assign_default_role(session: Any, user_id: UUID) -> None:
    """Assign the default role to a newly created user (best-effort)."""
    from sqlalchemy import select

    stmt = select(Role).where(Role.slug == DEFAULT_ROLE_SLUG)
    result = await session.execute(stmt)
    default_role = result.scalar_one_or_none()

    if default_role is None:
        logger.warning(
            "Default role '%s' not found — skipping role assignment", DEFAULT_ROLE_SLUG
        )
        return

    session.add(UserRole(user_id=user_id, role_id=default_role.id))


async def get_user_by_email(email: str) -> User | None:
    """Retrieve a user by email address."""
    async with alchemy.get_session() as session:
        service = UsersService(session=session)
        return await service.get_one_or_none(email=email)


async def get_user_by_id(user_id: str | UUID) -> User | None:
    """Retrieve a user by ID."""
    async with alchemy.get_session() as session:
        service = UsersService(session=session)
        return await service.get_one_or_none(id=user_id)
