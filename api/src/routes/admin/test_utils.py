"""Test utility endpoints for e2e testing.

Provides:
    - /test/errors (GET / reset POST) — in-memory error collector access.
    - /test/cleanup (POST) — bulk-delete records created by e2e tests
      (matched by name/system_name prefix).
    - /test/promote (POST) — mark a user `is_superuser=True` so Cypress
      can hit admin routes without role seeding.

Only registered when DEBUG_MODE=True. Never expose in production.
"""

from __future__ import annotations

from typing import Any

from litestar import Controller, get, post
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.server.test_error_collector import get_collector


class PromoteRequest(BaseModel):
    email: str


# Tables that hold e2e-test-* records. Each has `name` and/or `system_name`
# columns. Kept explicit (no reflection) to avoid accidentally wiping
# tables with operational data (users, jobs, metrics, ...).
#
# For each table, list the columns we can prefix-match on. `name` is the
# user-facing title, `system_name` is the unique slug.
CLEANUP_TABLES: dict[str, list[str]] = {
    "prompts": ["name", "system_name"],
    "rag_tools": ["name", "system_name"],
    "retrieval_tools": ["name", "system_name"],
    "collections": ["name", "system_name"],
    "agents": ["name", "system_name"],
    "ai_apps": ["name", "system_name"],
    "mcp_servers": ["name", "system_name"],
    "providers": ["name", "system_name"],
    "ai_models": ["name", "system_name"],
    "api_keys": ["name"],  # no system_name column
    "api_servers": ["name", "system_name"],
    "api_tools": ["name", "system_name"],
    "evaluation_sets": ["name", "system_name"],
    "knowledge_graphs": ["name", "system_name"],
}


class TestUtilsController(Controller):
    path = "/test"
    tags = ["test-utils"]

    @get("/errors", exclude_from_auth=True)
    async def get_errors(self) -> list[dict]:
        """Return all collected backend errors since last reset."""
        return get_collector().get_all()

    @post("/errors/reset", exclude_from_auth=True)
    async def reset_errors(self) -> None:
        """Clear the collected errors. Call before each test."""
        get_collector().reset()

    @post(
        "/cleanup",
        status_code=200,
        exclude_from_auth=True,
    )
    async def cleanup(
        self,
        db_session: AsyncSession,
        prefix: str = Parameter(
            default="e2e-test-",
            description="Prefix matched against name and system_name columns. "
            "Only matching rows are deleted. Must be non-empty to prevent "
            "accidental table-wide wipes.",
        ),
    ) -> dict[str, Any]:
        """Bulk-delete e2e-test-* records across known CRUD tables.

        POST (not DELETE) so the query-string parameter travels reliably
        through clients that disallow bodies on DELETE. Returns a per-table
        count of deleted rows.

        Safety: `prefix` must be non-empty (reject "" and lone "%").
        """
        if not prefix or prefix in ("%", "_"):
            raise ValueError(
                "prefix must be a non-empty literal (got %r) — refusing to run "
                "a catch-all delete" % prefix
            )

        # Escape SQL LIKE metacharacters in the prefix so callers can pass
        # literal strings without the % or _ being treated as wildcards.
        safe_prefix = (
            prefix.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        )
        pattern = f"{safe_prefix}%"

        result: dict[str, Any] = {}
        for table, cols in CLEANUP_TABLES.items():
            where = " OR ".join(f"{c} LIKE :pattern ESCAPE '\\'" for c in cols)
            stmt = text(f"DELETE FROM {table} WHERE {where}")
            try:
                out = await db_session.execute(stmt, {"pattern": pattern})
                result[table] = out.rowcount or 0
            except Exception as e:  # noqa: BLE001
                result[table] = -1
                result[f"{table}__error"] = str(e)

        await db_session.commit()
        return {"prefix": prefix, "deleted": result}

    @post(
        "/promote",
        status_code=200,
        exclude_from_auth=True,
    )
    async def promote(
        self,
        db_session: AsyncSession,
        data: PromoteRequest,
    ) -> dict[str, Any]:
        """Flip `is_superuser=True` AND assign the `admin` role to an
        existing user by email.

        Used by Cypress to promote the E2E test user so admin routes
        become reachable. The admin role is required because the FE's
        `hasAdminAccess` check inspects `user.roles` (not `is_superuser`).
        Idempotent — no-op if flag/role already set.
        """
        stmt = text(
            "UPDATE user_account SET is_superuser = TRUE, is_verified = TRUE, "
            "is_active = TRUE WHERE email = :email RETURNING id"
        )
        out = await db_session.execute(stmt, {"email": data.email})
        row = out.first()
        if row is None:
            raise NotFoundException(f"No user with email={data.email}")
        user_id = row[0]

        # Assign admin role (idempotent — duplicate (user_id,role_id)
        # pairs prevented by the uq_user_role unique constraint).
        # `role.slug = 'admin'` is seeded by the app.
        await db_session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id, assigned_at, "
                "created_at, updated_at) "
                "SELECT gen_random_uuid(), :user_id, id, NOW(), NOW(), NOW() "
                "FROM role WHERE slug = 'admin' "
                "ON CONFLICT ON CONSTRAINT uq_user_role DO NOTHING"
            ),
            {"user_id": user_id},
        )
        await db_session.commit()
        return {
            "email": data.email,
            "user_id": str(user_id),
            "is_superuser": True,
            "role": "admin",
        }
