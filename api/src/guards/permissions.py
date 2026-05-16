"""
Permission-based access control.

Source of truth for the permission **codes** is the `Permission` enum. The
catalog is mirrored into the `permission` DB table (seeded by alembic) so
the upcoming admin UI (PR 5) can render the resource × action matrix and
`role_permission` can have a real FK.

Role → permission mapping:
- After PR 2 the DB is authoritative. `_ROLE_PERMISSIONS_CACHE` holds a
  process-wide snapshot loaded from `role_permission` once.
- `SYSTEM_ROLE_DEFAULTS` remains the in-code fallback. Used when the cache
  hasn't loaded yet (boot, tests without seeded DB) — same set as the
  migration seeds, so behaviour is identical.

`require_permission(...)` returns a Litestar Guard. It requires ALL listed
permissions. For "any-of" semantics use `require_any_permission(...)`.

API-key auth: scopes on the key are treated as the effective permission set
(capability ceiling). The user's role permissions are NOT unioned in — that
would break the ceiling.
"""

from __future__ import annotations

import logging
import threading
from enum import StrEnum
from typing import TYPE_CHECKING

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler
from litestar.types import Guard

if TYPE_CHECKING:
    from middlewares.auth import Auth

logger = logging.getLogger(__name__)


class Permission(StrEnum):
    # Agents (pilot)
    AGENTS_READ = "read:agents"
    AGENTS_WRITE = "write:agents"
    AGENTS_DELETE = "delete:agents"
    AGENTS_EXECUTE = "execute:agents"
    AGENTS_SHARE = "share:agents"

    # AI Apps
    AI_APPS_READ = "read:ai_apps"
    AI_APPS_WRITE = "write:ai_apps"
    AI_APPS_DELETE = "delete:ai_apps"

    # Collections
    COLLECTIONS_READ = "read:collections"
    COLLECTIONS_WRITE = "write:collections"
    COLLECTIONS_DELETE = "delete:collections"

    # Prompts
    PROMPTS_READ = "read:prompts"
    PROMPTS_WRITE = "write:prompts"
    PROMPTS_DELETE = "delete:prompts"

    # Knowledge Graph
    KNOWLEDGE_GRAPH_READ = "read:knowledge_graph"
    KNOWLEDGE_GRAPH_WRITE = "write:knowledge_graph"
    KNOWLEDGE_GRAPH_DELETE = "delete:knowledge_graph"

    # RAG / retrieval tools
    RAG_TOOLS_READ = "read:rag_tools"
    RAG_TOOLS_WRITE = "write:rag_tools"
    RAG_TOOLS_DELETE = "delete:rag_tools"

    RETRIEVAL_TOOLS_READ = "read:retrieval_tools"
    RETRIEVAL_TOOLS_WRITE = "write:retrieval_tools"
    RETRIEVAL_TOOLS_DELETE = "delete:retrieval_tools"

    # MCP / API servers
    MCP_SERVERS_READ = "read:mcp_servers"
    MCP_SERVERS_WRITE = "write:mcp_servers"
    MCP_SERVERS_DELETE = "delete:mcp_servers"

    API_SERVERS_READ = "read:api_servers"
    API_SERVERS_WRITE = "write:api_servers"
    API_SERVERS_DELETE = "delete:api_servers"

    # Evaluations / deep research / prompt queue
    EVALUATIONS_READ = "read:evaluations"
    EVALUATIONS_WRITE = "write:evaluations"

    DEEP_RESEARCH_READ = "read:deep_research"
    DEEP_RESEARCH_WRITE = "write:deep_research"

    PROMPT_QUEUE_READ = "read:prompt_queue"
    PROMPT_QUEUE_WRITE = "write:prompt_queue"

    # Files / jobs / traces / observability
    FILES_READ = "read:files"
    FILES_WRITE = "write:files"

    JOBS_READ = "read:jobs"
    JOBS_WRITE = "write:jobs"

    OBSERVABILITY_READ = "read:observability"

    # Note taker (transcripts, recordings)
    NOTE_TAKER_READ = "read:note_taker"
    NOTE_TAKER_WRITE = "write:note_taker"

    # AI models / providers / settings / catalog
    AI_MODELS_READ = "read:ai_models"
    AI_MODELS_WRITE = "write:ai_models"

    PROVIDERS_READ = "read:providers"
    PROVIDERS_WRITE = "write:providers"

    SETTINGS_READ = "read:settings"
    SETTINGS_WRITE = "write:settings"

    # Governance / admin
    ROLES_READ = "read:roles"
    ROLES_WRITE = "write:roles"

    USERS_READ = "read:users"
    USERS_MANAGE = "manage:users"

    GROUPS_READ = "read:groups"
    GROUPS_WRITE = "write:groups"

    API_KEYS_READ = "read:api_keys"
    API_KEYS_WRITE = "write:api_keys"

    RESOURCE_ACCESS_MANAGE = "manage:resource_access"
    AUDIT_READ = "read:audit"


_ALL_PERMISSIONS: frozenset[str] = frozenset(p.value for p in Permission)

_READ_PERMISSIONS: frozenset[str] = frozenset(
    p.value for p in Permission if p.value.startswith("read:")
)

# System role defaults. Role slug → permission codes.
# Custom tenant roles will be DB-backed (see PR 2 in the plan); for now this
# dict is the only source of role→permission mapping.
SYSTEM_ROLE_DEFAULTS: dict[str, frozenset[str]] = {
    "admin": _ALL_PERMISSIONS,
    "user": frozenset(
        {
            Permission.AGENTS_READ.value,
            Permission.AGENTS_EXECUTE.value,
            Permission.AI_APPS_READ.value,
            Permission.COLLECTIONS_READ.value,
            Permission.PROMPTS_READ.value,
            Permission.KNOWLEDGE_GRAPH_READ.value,
            Permission.RAG_TOOLS_READ.value,
            Permission.RETRIEVAL_TOOLS_READ.value,
            Permission.MCP_SERVERS_READ.value,
            Permission.API_SERVERS_READ.value,
            Permission.FILES_READ.value,
            Permission.FILES_WRITE.value,
            Permission.JOBS_READ.value,
            Permission.AI_MODELS_READ.value,
            Permission.NOTE_TAKER_READ.value,
            Permission.NOTE_TAKER_WRITE.value,
        }
    ),
    "viewer": _READ_PERMISSIONS,
}


# Process-wide snapshot of role → permission codes loaded from DB on startup.
# `None` means "not loaded yet" → use SYSTEM_ROLE_DEFAULTS fallback.
_ROLE_PERMISSIONS_CACHE: dict[str, frozenset[str]] | None = None
_CACHE_LOCK = threading.Lock()


def _role_permissions(slug: str) -> frozenset[str]:
    """Look up the granted permissions for a role slug.

    DB cache wins when loaded. Falls back to SYSTEM_ROLE_DEFAULTS otherwise so
    that startup, tests, and auth-disabled flows continue to work.
    """
    cache = _ROLE_PERMISSIONS_CACHE
    if cache is not None:
        return cache.get(slug, frozenset())
    return SYSTEM_ROLE_DEFAULTS.get(slug, frozenset())


async def load_role_permissions_cache(session=None) -> None:
    """Populate `_ROLE_PERMISSIONS_CACHE` from the `role_permission` table.

    Called from app startup. Safe to call multiple times — last write wins.
    If the DB schema isn't migrated yet (no `role_permission` table) we log
    and leave the cache empty so the in-code fallback keeps things up.

    `session` is optional: pass an `AsyncSession` to reuse a known DB
    connection (useful for tests and for the admin role-edit endpoint after
    it commits its changes). When `None`, we open a fresh session via the
    process-wide alchemy factory.
    """
    global _ROLE_PERMISSIONS_CACHE

    try:
        from core.db.models.user.role import Role
        from core.db.models.user.role_permission import RolePermission
        from sqlalchemy import select
    except Exception:  # noqa: BLE001 - import errors are fatal at boot, not here
        logger.warning("Permission cache: deps not importable, using in-code defaults")
        return

    grants: dict[str, set[str]] = {}
    try:
        stmt = select(Role.slug, RolePermission.permission_code).join(
            RolePermission, RolePermission.role_id == Role.id
        )
        if session is not None:
            result = await session.execute(stmt)
        else:
            from core.config.app import alchemy

            async with alchemy.get_session() as s:
                result = await s.execute(stmt)
        for slug, code in result.all():
            grants.setdefault(slug, set()).add(code)
    except Exception:  # noqa: BLE001
        logger.warning(
            "Permission cache: DB lookup failed, falling back to in-code defaults",
            exc_info=True,
        )
        return

    snapshot = {slug: frozenset(codes) for slug, codes in grants.items()}
    with _CACHE_LOCK:
        _ROLE_PERMISSIONS_CACHE = snapshot
    logger.info(
        "Permission cache loaded: %d role(s), %d total grants",
        len(snapshot),
        sum(len(v) for v in snapshot.values()),
    )


def reset_role_permissions_cache() -> None:
    """Drop the cache. Call from admin role-edit endpoints to force reload."""
    global _ROLE_PERMISSIONS_CACHE
    with _CACHE_LOCK:
        _ROLE_PERMISSIONS_CACHE = None


def get_effective_permissions(auth: "Auth | None") -> set[str]:
    """Compute the effective permission set for the current principal.

    Order:
    1. Unauthenticated → empty.
    2. DB user with `is_superuser=True` → all permissions.
    3. API key auth → key scopes (capability ceiling; role perms NOT unioned).
       Missing scopes fail closed.
    4. JWT/session user → union over user.roles via `_role_permissions()`,
       which reads from the DB cache (or SYSTEM_ROLE_DEFAULTS fallback);
       fallback to auth.data["roles"] if DB user is not loaded.
    """
    if auth is None:
        return set()

    user = getattr(auth, "user", None)
    if user is not None and getattr(user, "is_superuser", False):
        return set(_ALL_PERMISSIONS)

    if auth.type == "api_key":
        scopes = auth.data.get("scopes")
        if scopes is None:
            return set()
        if isinstance(scopes, str):
            scopes = [scopes]
        return {str(s) for s in scopes}

    role_slugs: set[str] = set()
    if user is not None and getattr(user, "roles", None):
        role_slugs.update(r.slug for r in user.roles)
    else:
        token_roles = auth.data.get("roles") if auth.data else None
        if isinstance(token_roles, (list, set, tuple)):
            role_slugs.update(str(r) for r in token_roles)
        elif isinstance(token_roles, str):
            role_slugs.add(token_roles)

    result: set[str] = set()
    for slug in role_slugs:
        result.update(_role_permissions(slug))
    return result


def _check(connection: ASGIConnection, required: frozenset[str], any_of: bool) -> None:
    auth = connection.scope.get("auth")
    if not auth:
        # Mirror the existing pattern: when auth is disabled in this process
        # (test app, internal admin scripts), router-level role guards are
        # never attached. Fall through so per-endpoint permission guards
        # behave the same way and don't break auth-disabled tests.
        from core.config.base import get_auth_settings

        if not get_auth_settings().AUTH_ENABLED:
            return
        raise PermissionDeniedException("Authentication required.")

    effective = get_effective_permissions(auth)

    if any_of:
        if effective & required:
            return
        raise PermissionDeniedException(
            f"Requires one of permissions: {', '.join(sorted(required))}"
        )

    missing = required - effective
    if not missing:
        return
    raise PermissionDeniedException(
        f"Missing permission(s): {', '.join(sorted(missing))}"
    )


def require_permission(*required: str | Permission) -> Guard:
    """Guard that requires the principal to hold ALL listed permissions."""
    required_set = frozenset(str(r) for r in required)
    if not required_set:
        raise ValueError("require_permission() needs at least one permission")

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        _check(connection, required_set, any_of=False)

    return guard


def require_any_permission(*required: str | Permission) -> Guard:
    """Guard that requires the principal to hold AT LEAST ONE of listed permissions."""
    required_set = frozenset(str(r) for r in required)
    if not required_set:
        raise ValueError("require_any_permission() needs at least one permission")

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        _check(connection, required_set, any_of=True)

    return guard
