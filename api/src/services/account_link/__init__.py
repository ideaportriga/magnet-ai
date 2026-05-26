"""Generic out-of-band account-link flow.

Any external surface that wants to bind a remote identity to a user_account
calls :func:`issue_link_code` (passing ``provider``/``subject_id`` and
optional channel context). The user then enters that code in the admin UI;
the backend resolves it via :func:`preview_link_code` / :func:`consume_link_code`.

Channel-specific cleanup (e.g. Teams backfilling ``teams_user.tenant_id``)
plugs in via :func:`register_post_consume_hook` — keep this module provider-
and channel-agnostic.
"""

from .post_consume import (
    PostConsumeHook,
    PostConsumeHookContext,
    register_post_consume_hook,
)
from .service import (
    IssuedLinkCode,
    LinkCodeAlreadyBound,
    LinkCodeError,
    LinkCodeNotFound,
    LinkCodePreview,
    LinkedAccount,
    LinkedAccountNotFound,
    LINK_CODE_TTL,
    admin_list_linked_accounts,
    admin_revoke_linked_account,
    cleanup_expired_link_codes,
    consume_link_code,
    issue_link_code,
    list_linked_accounts,
    preview_link_code,
    revoke_linked_account,
)

__all__ = [
    "IssuedLinkCode",
    "LinkCodeAlreadyBound",
    "LinkCodeError",
    "LinkCodeNotFound",
    "LinkCodePreview",
    "LinkedAccount",
    "LinkedAccountNotFound",
    "LINK_CODE_TTL",
    "PostConsumeHook",
    "PostConsumeHookContext",
    "admin_list_linked_accounts",
    "admin_revoke_linked_account",
    "cleanup_expired_link_codes",
    "consume_link_code",
    "issue_link_code",
    "list_linked_accounts",
    "preview_link_code",
    "register_post_consume_hook",
    "revoke_linked_account",
]
