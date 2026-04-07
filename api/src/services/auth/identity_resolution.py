"""
Identity Resolution Service — maps external identities to internal users.

This is the central point where all external identity sources (OIDC, OAuth,
local auth) are resolved to a single internal User record.
"""

from __future__ import annotations

from datetime import UTC, datetime
from logging import getLogger
from typing import Any
from uuid import UUID

from sqlalchemy import select

from core.db.models.user.role import Role
from core.db.models.user.user import User
from core.db.models.user.user_oauth_account import UserOAuthAccount
from core.db.models.user.user_role import UserRole
from core.domain.users.service import UsersService
from core.exceptions import AuthError
from guards.role import DEFAULT_ROLE_SLUG
from services.auth.types import ExternalIdentity

logger = getLogger(__name__)


async def resolve_identity(
    session: Any,
    identity: ExternalIdentity,
) -> User:
    """Resolve an external identity to an internal user.

    Rules:
    1. Find user_oauth_account by (provider, subject_id) → return linked user
    2. Find user by email with email_verified from IdP → auto-link
    3. Find user by email WITHOUT email_verified → reject (account takeover protection)
    4. No user found → create new user + link

    Args:
        session: SQLAlchemy async session.
        identity: Verified external identity from an identity strategy.

    Returns:
        The internal User (created or found).

    Raises:
        AuthError: If identity cannot be safely resolved.
    """
    now = datetime.now(UTC)
    service = UsersService(session=session)

    # 1. Try to find existing link by (provider, subject_id)
    stmt = select(UserOAuthAccount).where(
        UserOAuthAccount.oauth_name == identity.provider,
        UserOAuthAccount.account_id == identity.subject_id,
    )
    result = await session.execute(stmt)
    existing_link = result.scalar_one_or_none()

    if existing_link is not None:
        # Known identity — load and update user
        user = await service.get_one_or_none(id=existing_link.user_id)
        if user is None:
            raise AuthError("Linked user not found")

        user.last_login_at = now
        if identity.name and user.name != identity.name:
            user.name = identity.name
        existing_link.last_login_at = now
        if identity.email and existing_link.account_email != identity.email:
            existing_link.account_email = identity.email

        # Sync suggested roles if provider offers them
        if identity.suggested_roles:
            await _sync_suggested_roles(session, user.id, identity.suggested_roles)

        return user

    # 2. Try to find user by email
    user = await service.get_one_or_none(email=identity.email)

    if user is not None:
        # User exists — only auto-link if email is verified by the provider
        if not identity.email_verified:
            logger.warning(
                "Refusing to auto-link %s/%s to existing user %s: email not verified by provider",
                identity.provider,
                identity.subject_id,
                user.email,
            )
            raise AuthError(
                "Cannot link account: email not verified by identity provider"
            )

        # Auto-link: verified email matches existing user
        user.last_login_at = now
        if identity.name and user.name != identity.name:
            user.name = identity.name

        _create_identity_link(session, user.id, identity, now)

        if identity.suggested_roles:
            await _sync_suggested_roles(session, user.id, identity.suggested_roles)

        logger.info(
            "Auto-linked %s/%s to existing user %s (verified email match)",
            identity.provider,
            identity.subject_id,
            user.email,
        )
        return user

    # 3. Create new user
    user = await service.create(
        User(
            email=identity.email,
            name=identity.name,
            is_active=True,
            is_verified=identity.email_verified,
            last_login_at=now,
        ),
        auto_commit=False,
    )

    await _assign_default_role(session, user.id)
    _create_identity_link(session, user.id, identity, now)

    if identity.suggested_roles:
        await _sync_suggested_roles(session, user.id, identity.suggested_roles)

    logger.info("Created new user from %s: %s", identity.provider, identity.email)
    return user


def _create_identity_link(
    session: Any,
    user_id: UUID,
    identity: ExternalIdentity,
    now: datetime,
) -> None:
    """Create a UserOAuthAccount link for the identity."""
    session.add(
        UserOAuthAccount(
            user_id=user_id,
            oauth_name=identity.provider,
            account_id=identity.subject_id,
            account_email=identity.email,
            last_login_at=now,
        )
    )


async def _assign_default_role(session: Any, user_id: UUID) -> None:
    """Assign the default role to a newly created user."""
    stmt = select(Role).where(Role.slug == DEFAULT_ROLE_SLUG)
    result = await session.execute(stmt)
    default_role = result.scalar_one_or_none()
    if default_role is None:
        logger.warning("Default role '%s' not found", DEFAULT_ROLE_SLUG)
        return
    session.add(UserRole(user_id=user_id, role_id=default_role.id))


async def _sync_suggested_roles(
    session: Any, user_id: UUID, suggested_slugs: list[str]
) -> None:
    """Additively sync roles suggested by an IdP.

    Only adds missing roles — never removes existing ones.
    This is the safe default. Per-provider override policies can be added later.
    """
    role_slugs = set(suggested_slugs) | {DEFAULT_ROLE_SLUG}

    # Get matching roles from DB
    stmt = select(Role).where(Role.slug.in_(role_slugs))
    result = await session.execute(stmt)
    target_roles = {r.slug: r.id for r in result.scalars().all()}

    # Get current user roles
    stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
    result = await session.execute(stmt)
    current_role_ids = {r[0] for r in result.fetchall()}

    # Add missing roles (additive only)
    for slug, role_id in target_roles.items():
        if role_id not in current_role_ids:
            session.add(UserRole(user_id=user_id, role_id=role_id))
            logger.info("Added suggested role '%s' for user %s", slug, user_id)
