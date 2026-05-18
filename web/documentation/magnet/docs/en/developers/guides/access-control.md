# Access control for developers

This page is for engineers extending the API or writing new
resource endpoints. For an admin-side view of the RBAC model see
[Admin → Access control](../../admin/access/overview).

## Layers

The platform stacks three layers from coarse to fine:

1. **Authentication** — `middlewares/auth.py` resolves the
   principal into an `Auth` object on every ASGI scope. JWT
   sessions, API keys, and OAuth tokens all funnel through the
   same shape.
2. **Capability ceiling** — route guards in
   `guards/permissions.py` check that the principal holds the
   permission codes declared on each handler
   (`require_permission(Permission.RAG_TOOLS_WRITE)`).
3. **Record-level rules** — `services/access_control` narrows
   visibility within the ceiling: owner, visibility, department
   membership, and explicit resource-access grants.

Skip any layer and you leak data — every controller has to compose
all three. The `services/access_control/record_level.py` helpers
make that composition mechanical.

## Route guards

Attach the guard at the handler level:

```python
from litestar import Controller, get
from guards.permissions import Permission, require_permission

class AgentsController(Controller):
    path = "/agents"

    @get(
        "/",
        guards=[require_permission(Permission.AGENTS_READ)],
    )
    async def list_agents(self, ...): ...
```

Multiple permissions are AND-ed by default. For OR semantics use
`require_any_permission(...)`. When auth is disabled
(`AUTH_ENABLED=false` in test apps) the guards no-op — record-level
helpers do the same.

### API keys

API-key auth treats the key's `scopes` list as the **complete**
effective permission set. Role unioning is deliberately disabled —
keys cannot exceed their declared scope, even if the owning user
later gains broader rights. This is enforced in
`get_effective_permissions()`.

## Adding a new resource type

To register a brand-new resource (say `widgets`) in the access
control system:

1. **Add permission codes** to the `Permission` enum in
   `guards/permissions.py`:

   ```python
   WIDGETS_READ = "read:widgets"
   WIDGETS_WRITE = "write:widgets"
   WIDGETS_DELETE = "delete:widgets"
   ```

   The `record_visibility_filter` SQL builder picks these up
   automatically because `_ACTION_TO_CAPABILITY` is dictionary-
   driven from the catalog.

2. **Seed system roles** in the migration that ships the new
   table. The pattern is to insert a `role_permission` row for the
   `admin` role for every code, and read-only ones for `viewer`.
   See migration `c5d6e7f8a9b0` for the template.

3. **Decide the record-level shape**. If you want per-record
   sharing, add three columns:

   ```python
   owner_id    = mapped_column(ForeignKey("user.id"), nullable=True)
   visibility  = mapped_column(String(32), default="tenant")
   department_id = mapped_column(ForeignKey("department.id"), nullable=True)
   ```

   …plus the tenant column you already need for RLS.

4. **Wire the controller** through the helpers in
   `services/access_control/record_level.py`:

   ```python
   from services.access_control import (
       create_with_record_context,
       enforce_view_or_404,
       list_with_record_permissions,
       update_with_record_access,
       delete_with_record_access,
   )
   ```

   The helpers do:

   - **Create**: stamp `tenant_id` + `owner_id` from auth, strip
     client-supplied identity fields.
   - **List**: append `record_visibility_filter()` to the WHERE.
   - **Get / update / delete**: load row, run
     `enforce_view_or_404` / `enforce_action_or_403`, raise the
     right HTTP code (404 for non-disclosure, 403 for explicit
     denials).
   - **Attach `_permissions`**: every response body has a
     per-record `{view, edit, delete, share}` boolean block so the
     UI can hide buttons without re-asking the API.

5. **Test**. A new resource needs at least:

   - Capability ceiling rejections (no permission ⇒ 403).
   - Cross-tenant denial (other tenant ⇒ 404).
   - Visibility transitions (private ↔ department ↔ tenant).
   - Grant evaluation (user / group / department).
   - List visibility (rows hidden, not just 403 on detail).

   The existing agents and RAG-tools test suites are the canonical
   templates.

## Permission cache

Role → permission codes are loaded once at startup into
`_ROLE_PERMISSIONS_CACHE`. Whenever an admin endpoint changes a
role's permissions or deletes a role, the cache is reset
(`reset_role_permissions_cache()`); the next request will re-read
from `role_permission`. The cache lives per-process, so on
multi-worker deployments each worker reloads independently — the
reset happens through Litestar's startup hook on each.

Out-of-band updates (e.g. running SQL directly against
`role_permission`) won't be picked up until the workers restart.

## Audit logging

Use `services.access_control.write_audit_log(...)` for any
governance-relevant mutation:

```python
await write_audit_log(
    session,
    actor_id=auth.user.id,
    action="role.permissions.replace",
    target_type="role",
    target_id=role.id,
    payload={"added": added, "removed": removed},
    trace_id=request.scope.get("trace_id"),
)
```

The writer is fire-and-forget on the same DB session as the change
itself, so the row is part of the same transaction — either both
the change and the audit record commit, or neither does.

## Useful files at a glance

| File | What it owns |
|---|---|
| `api/src/guards/permissions.py` | `Permission` enum, route guards, role cache. |
| `api/src/services/access_control/permissions.py` | `PermissionService.can()` algorithm, `record_visibility_filter` SQL builder. |
| `api/src/services/access_control/record_level.py` | Controller helpers. |
| `api/src/services/access_control/audit.py` | `write_audit_log()`. |
| `api/src/routes/admin/users.py`, `roles.py`, `permissions.py`, `access_log.py` | Admin REST endpoints consumed by the UI. |
| `api/src/core/db/models/user/role.py` | Role table (system vs custom invariants). |
| `api/src/core/db/models/access_grant/resource_access_grant.py` | Per-record ACL rows. |
