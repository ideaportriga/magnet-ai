"""Issue / preview / consume short-lived account-link pairing codes.

Provider- and channel-agnostic. The only thing this module knows is that a
pairing code, once consumed, results in a ``user_account_oauth`` row binding
``(provider, subject_id) → user_account.id``. Channel-specific cleanup is
delegated to ``post_consume`` hooks keyed by ``channel_kind``.
"""

from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, delete, select

from core.db.models.oauth import AccountLinkCode
from core.db.models.user.user_oauth_account import UserOAuthAccount
from core.db.rls_context import rls_context_scope
from core.db.session import async_session_maker
from services.access_control import write_audit_log

from .post_consume import PostConsumeHookContext, run_post_consume_hook

logger = getLogger(__name__)


# Crockford-base32 alphabet minus I/L/O/U to avoid visual ambiguity. 30
# symbols × 12 chars ≈ 59 bits of entropy — well above brute-force range
# for a 10-minute TTL with rate limits.
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_CODE_GROUPS = 3
_CODE_GROUP_LEN = 4

LINK_CODE_TTL = dt.timedelta(minutes=10)


def _generate_code() -> str:
    raw = "".join(
        secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_GROUPS * _CODE_GROUP_LEN)
    )
    return "-".join(
        raw[i : i + _CODE_GROUP_LEN] for i in range(0, len(raw), _CODE_GROUP_LEN)
    )


def _normalize_code(value: str) -> str:
    """Accept user-typed codes case-insensitively, ignore stray whitespace."""
    return (value or "").strip().upper()


@dataclass(frozen=True, slots=True)
class IssuedLinkCode:
    code: str
    expires_at: dt.datetime


@dataclass(frozen=True, slots=True)
class LinkedAccount:
    """A current ``user_account_oauth`` binding, as shown to the owning user."""

    id: UUID
    provider: str
    account_id: str
    account_email: Optional[str]
    last_login_at: Optional[dt.datetime]
    created_at: Optional[dt.datetime]


class LinkedAccountNotFound(Exception):
    """Revoke target not found, or belongs to a different user."""


@dataclass(frozen=True, slots=True)
class LinkCodePreview:
    code: str
    provider: str
    channel_kind: Optional[str]
    display_name: Optional[str]
    email: Optional[str]
    extra: Optional[dict[str, Any]]
    expires_at: dt.datetime


class LinkCodeError(Exception):
    """Base for link-code domain errors. Subclasses map to HTTP status codes."""


class LinkCodeNotFound(LinkCodeError):
    """Code unknown, expired, or already consumed."""


class LinkCodeAlreadyBound(LinkCodeError):
    """The external identity is already bound to a different user_account."""


async def issue_link_code(
    *,
    provider: str,
    subject_id: str,
    channel_kind: str | None = None,
    channel_id: str | None = None,
    display_name: str | None = None,
    email: str | None = None,
    extra: dict[str, Any] | None = None,
) -> IssuedLinkCode:
    """Generate a code, invalidating any prior active code for the same target.

    "Same target" = ``(provider, subject_id, channel_id)`` — see the partial
    unique index ``uq_account_link_code_active``. The pre-insert DELETE
    matches that key and keeps "newest /link wins" semantics.

    Runs under a superuser RLS scope: ``account_link_code`` itself has no
    RLS (it's pre-auth), but ``user_account_oauth`` reads in ``consume`` do,
    and using the same scope here keeps the surface consistent.
    """
    now = dt.datetime.now(dt.timezone.utc)
    expires_at = now + LINK_CODE_TTL
    code = _generate_code()

    with rls_context_scope(tenant_id=None, is_superuser=True):
        async with async_session_maker() as session:
            try:
                await session.execute(
                    delete(AccountLinkCode).where(
                        AccountLinkCode.provider == provider,
                        AccountLinkCode.subject_id == subject_id,
                        # COALESCE-style match the partial index uses.
                        (AccountLinkCode.channel_id == channel_id)
                        if channel_id is not None
                        else AccountLinkCode.channel_id.is_(None),
                        AccountLinkCode.consumed_at.is_(None),
                    )
                )
                row = AccountLinkCode(
                    code=code,
                    provider=provider,
                    subject_id=subject_id,
                    channel_kind=channel_kind,
                    channel_id=channel_id,
                    display_name=display_name,
                    email=email,
                    extra=extra,
                    expires_at=expires_at,
                )
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return IssuedLinkCode(code=code, expires_at=expires_at)


async def preview_link_code(code: str) -> LinkCodePreview:
    normalized = _normalize_code(code)
    if not normalized:
        raise LinkCodeNotFound()

    now = dt.datetime.now(dt.timezone.utc)
    with rls_context_scope(tenant_id=None, is_superuser=True):
        async with async_session_maker() as session:
            stmt = select(AccountLinkCode).where(
                AccountLinkCode.code == normalized,
                AccountLinkCode.consumed_at.is_(None),
                AccountLinkCode.expires_at > now,
            )
            row = (await session.execute(stmt)).scalars().first()

    if row is None:
        raise LinkCodeNotFound()

    return LinkCodePreview(
        code=row.code,
        provider=row.provider,
        channel_kind=row.channel_kind,
        display_name=row.display_name,
        email=row.email,
        extra=row.extra,
        expires_at=row.expires_at,
    )


async def cleanup_expired_link_codes(
    *, older_than: dt.timedelta = dt.timedelta(hours=24)
) -> int:
    """Remove `account_link_code` rows past their expiry by ``older_than``.

    Returns the number of deleted rows. Intended for nightly cron. Codes are
    short-lived anyway, but expired rows accumulate forever otherwise (the
    partial unique index `uq_account_link_code_active` ignores consumed/expired
    rows, so they don't block new `/link` requests — but they bloat the table).
    """
    cutoff = dt.datetime.now(dt.timezone.utc) - older_than
    with rls_context_scope(tenant_id=None, is_superuser=True):
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    delete(AccountLinkCode).where(AccountLinkCode.expires_at < cutoff)
                )
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("cleanup_expired_link_codes failed")
                raise
    deleted = int(getattr(result, "rowcount", 0) or 0)
    if deleted:
        logger.info(
            "cleanup_expired_link_codes: deleted %d row(s) older than %s",
            deleted,
            cutoff.isoformat(),
        )
    return deleted


async def list_linked_accounts(
    *, user_id: UUID, user_tenant_id: UUID
) -> list[LinkedAccount]:
    """List all OAuth-identity bindings owned by ``user_id``.

    The list is the user's own view, so we scope the query under their
    tenant — no superuser bypass needed.
    """
    with rls_context_scope(tenant_id=str(user_tenant_id), user_id=str(user_id)):
        async with async_session_maker() as session:
            stmt = (
                select(UserOAuthAccount)
                .where(UserOAuthAccount.user_id == user_id)
                .order_by(UserOAuthAccount.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()

    return [
        LinkedAccount(
            id=row.id,
            provider=row.oauth_name,
            account_id=row.account_id,
            account_email=row.account_email,
            last_login_at=row.last_login_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


async def admin_list_linked_accounts(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    user_id: UUID | None = None,
) -> list[LinkedAccount]:
    """Admin view: every binding in ``tenant_id``, optionally filtered by user.

    Caller must already hold the right permission (the route guard handles
    that). RLS keeps the result restricted to the caller's tenant — the
    ``tenant_id`` arg is forwarded into the scope, not into the WHERE.
    """
    with rls_context_scope(tenant_id=str(tenant_id), user_id=str(actor_id)):
        async with async_session_maker() as session:
            stmt = select(UserOAuthAccount)
            if user_id is not None:
                stmt = stmt.where(UserOAuthAccount.user_id == user_id)
            stmt = stmt.order_by(UserOAuthAccount.created_at.asc())
            rows = (await session.execute(stmt)).scalars().all()

    return [
        LinkedAccount(
            id=row.id,
            provider=row.oauth_name,
            account_id=row.account_id,
            account_email=row.account_email,
            last_login_at=row.last_login_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


async def admin_revoke_linked_account(
    *,
    link_id: UUID,
    tenant_id: UUID,
    actor_id: UUID,
) -> None:
    """Admin-side revoke. Deletes any binding within ``tenant_id``, regardless of owner."""
    with rls_context_scope(tenant_id=str(tenant_id), user_id=str(actor_id)):
        async with async_session_maker() as session:
            try:
                row = (
                    (
                        await session.execute(
                            select(UserOAuthAccount).where(
                                UserOAuthAccount.id == link_id
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if row is None:
                    raise LinkedAccountNotFound()
                snapshot = {
                    "provider": row.oauth_name,
                    "subject_id": row.account_id,
                    "account_email": row.account_email,
                    "owner_user_id": str(row.user_id),
                }
                await session.delete(row)
                await write_audit_log(
                    session,
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    action="account_link.admin_revoke",
                    target_type="user_account_oauth",
                    target_id=link_id,
                    payload=snapshot,
                )
                await session.commit()
            except LinkedAccountNotFound:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception(
                    "admin_revoke_linked_account failed link_id=%s actor=%s",
                    link_id,
                    actor_id,
                )
                raise


async def revoke_linked_account(
    *, link_id: UUID, user_id: UUID, user_tenant_id: UUID
) -> None:
    """Delete one of the user's OAuth bindings.

    Refuses if ``link_id`` doesn't belong to the calling user (covers
    typo / URL-tampering — RLS already covers cross-tenant attacks).
    """
    with rls_context_scope(tenant_id=str(user_tenant_id), user_id=str(user_id)):
        async with async_session_maker() as session:
            try:
                row = (
                    (
                        await session.execute(
                            select(UserOAuthAccount).where(
                                and_(
                                    UserOAuthAccount.id == link_id,
                                    UserOAuthAccount.user_id == user_id,
                                )
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if row is None:
                    raise LinkedAccountNotFound()
                # Snapshot before delete so the audit row has something to
                # reference once the source row is gone.
                snapshot = {
                    "provider": row.oauth_name,
                    "subject_id": row.account_id,
                    "account_email": row.account_email,
                }
                await session.delete(row)
                await write_audit_log(
                    session,
                    tenant_id=user_tenant_id,
                    actor_id=user_id,
                    action="account_link.revoke",
                    target_type="user_account_oauth",
                    target_id=link_id,
                    payload=snapshot,
                )
                await session.commit()
            except LinkedAccountNotFound:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception(
                    "revoke_linked_account failed for link_id=%s user_id=%s",
                    link_id,
                    user_id,
                )
                raise


async def consume_link_code(
    *,
    code: str,
    user_id: UUID,
    user_tenant_id: UUID,
) -> None:
    """Bind the external identity in ``code`` to ``user_id``.

    Atomically:
      1. Re-check the code is still valid (locks the row).
      2. Insert ``user_account_oauth(provider, subject_id) → user_id`` —
         no-op if the same user already has the binding.
      3. Run the channel-specific post-consume hook (if any).
      4. Mark the code as consumed.

    Raises:
      LinkCodeNotFound: code unknown, expired, or already consumed.
      LinkCodeAlreadyBound: ``(provider, subject_id)`` is already bound
        to a different user_account.
    """
    normalized = _normalize_code(code)
    if not normalized:
        raise LinkCodeNotFound()

    now = dt.datetime.now(dt.timezone.utc)

    # Superuser scope: this operation deliberately crosses tenants — the
    # consuming user's tenant may differ from any pre-existing channel-side
    # state (e.g. teams_user with tenant_id=NULL).
    with rls_context_scope(tenant_id=None, is_superuser=True):
        async with async_session_maker() as session:
            try:
                code_row = (
                    (
                        await session.execute(
                            select(AccountLinkCode)
                            .where(
                                AccountLinkCode.code == normalized,
                                AccountLinkCode.consumed_at.is_(None),
                                AccountLinkCode.expires_at > now,
                            )
                            .with_for_update()
                        )
                    )
                    .scalars()
                    .first()
                )
                if code_row is None:
                    raise LinkCodeNotFound()

                provider = code_row.provider
                subject_id = code_row.subject_id

                # Reject double-bind to a *different* user — silent rebind
                # would surprise the original owner. Same-user re-link is a
                # no-op (we still mark the code consumed).
                existing = (
                    (
                        await session.execute(
                            select(UserOAuthAccount.user_id).where(
                                UserOAuthAccount.oauth_name == provider,
                                UserOAuthAccount.account_id == subject_id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if existing is not None and str(existing) != str(user_id):
                    raise LinkCodeAlreadyBound()

                oauth_row: UserOAuthAccount | None = None
                if existing is None:
                    oauth_row = UserOAuthAccount(
                        tenant_id=user_tenant_id,
                        user_id=user_id,
                        oauth_name=provider,
                        account_id=subject_id,
                        account_email=code_row.email,
                        last_login_at=now,
                    )
                    session.add(oauth_row)
                    # Populate `oauth_row.id` so the audit row can reference it.
                    await session.flush()

                await run_post_consume_hook(
                    PostConsumeHookContext(
                        provider=provider,
                        subject_id=subject_id,
                        channel_kind=code_row.channel_kind,
                        channel_id=code_row.channel_id,
                        extra=code_row.extra,
                        user_id=user_id,
                        user_tenant_id=user_tenant_id,
                    ),
                    session,
                )

                code_row.consumed_at = now
                code_row.consumed_by_user_id = user_id

                # One audit row per consume, even on idempotent re-link — the
                # consume_at timestamp matters for forensics either way.
                await write_audit_log(
                    session,
                    tenant_id=user_tenant_id,
                    actor_id=user_id,
                    action="account_link.bind",
                    target_type="user_account_oauth",
                    target_id=oauth_row.id if oauth_row is not None else existing,
                    payload={
                        "provider": provider,
                        "subject_id": subject_id,
                        "channel_kind": code_row.channel_kind,
                        "channel_id": code_row.channel_id,
                        "idempotent": oauth_row is None,
                    },
                )

                await session.commit()
            except LinkCodeError:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                logger.exception(
                    "consume_link_code failed for user_id=%s code=%s",
                    user_id,
                    normalized,
                )
                raise
