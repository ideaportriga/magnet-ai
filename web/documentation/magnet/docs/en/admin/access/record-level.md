# Record-level access

Roles set the **capability ceiling** for a user — but within that
ceiling each individual record (an agent, a RAG tool, an AI App, a
document, …) carries its own access settings. This page covers the
three knobs that decide *who can see and modify a specific record*:
**visibility**, **owner**, and **resource-access grants**.

::: tip
If you only care about coarse, tenant-wide access (e.g. "can
anyone in marketing run agents?"), the [roles](./roles) and
[users](./users) pages are enough. Read on when you need
per-record sharing.
:::

## Visibility

Every shareable record exposes a **visibility** field with one of
three values:

| Value | Icon | Effect |
|---|---|---|
| `tenant` | 🌐 | Visible to **anyone in the tenant** who has the matching `read:*` permission. The default for most records. |
| `department` | 👥 | Visible only to members of the record's `department_id`. Department leads can also edit / delete / share. |
| `private` | 🔒 | Visible only to the **owner** and to principals named in an explicit grant. |

The record's visibility chip is shown in the details header next to
the record name; in the tooltip on the (i) icon you can also see the
owner and department.

Changing visibility requires the `share:<resource>` permission on
that resource type — e.g. `share:agents` for agents.

## Owner

Every record stamps the user who created it as **`owner_id`**. The
owner always retains the actions their role permits, regardless of
visibility — turning a record into `private` does *not* lock the
owner out of it.

`owner_id` is set automatically on create from the auth context and
cannot be tampered with through the API (the controllers strip
client-supplied `owner_id` from incoming payloads). Ownership
transfer is performed by the platform, not through the public UI.

## Resource-access grants

For narrower sharing inside a `private` or `department` record, add
**resource-access grants**. A grant binds three things:

1. A **resource** — `(resource_type, resource_id)`.
2. A **principal** — one of:
   - `user` + a user UUID
   - `group` + a group UUID
   - `department` + a department UUID
3. An **access level** — `read`, `write`, or `admin`.

The access level dictates which actions the grant permits within
the principal's existing capability ceiling:

| Level | Allows |
|---|---|
| `read` | view |
| `write` | view + edit |
| `admin` | view + edit + delete + share |

::: warning Grants narrow, never widen
A grant only matters when the principal has the corresponding
`read:*`/`write:*`/`delete:*` permission already. If your role has
no `write:agents`, an `admin` grant on a specific agent still won't
let you edit it.
:::

### When grants are checked

The permission service follows a deterministic order
(`api/src/services/access_control/permissions.py`):

1. Authenticated? Otherwise deny.
2. Same tenant as the record? Otherwise 404.
3. Holds the global `verb:resource` capability? Otherwise deny.
4. Is the user a tenant admin (system `admin` role)? **Allow.**
5. Is the user the record's owner? **Allow.**
6. `visibility=tenant` and action is `view`? **Allow.**
7. `visibility=department`, user is a member, and either action is
   `view` or membership has `is_lead=true`? **Allow.**
8. Highest matching grant level satisfies the action? **Allow.**
9. Otherwise: **deny**, returning 404 to avoid disclosing existence
   for view checks, or 403 for write/delete/share.

For list endpoints the same rules become a single SQL `WHERE`
clause so we don't N+1 through individual record checks
(`record_visibility_filter`).

## Where grants are managed

On the alpha branch grants are created and revoked through the
backend API:

```http
POST   /api/admin/resource-access
DELETE /api/admin/resource-access/{grant_id}
GET    /api/admin/resource-access?resource_type=...&resource_id=...
```

The corresponding admin UI panel ("Share" dialog on each record) is
on the roadmap. For now, integrations and scripts use these
endpoints directly — they require `manage:resource_access` (or
`share:<resource>` on the specific record).

All grant create/revoke calls write to the
[access log](./access-log) with action codes
`resource_access.grant` and `resource_access.revoke`, including the
principal and access level in the payload.

## Worked example

A "knowledge-curator" user in the `knowledge` department needs to
edit one specific RAG tool that belongs to a colleague:

1. The RAG tool's owner sets `visibility=private` so other
   departments can't browse it.
2. An admin (or the owner with `share:rag_tools`) creates a grant:

   ```json
   {
     "resource_type": "rag_tools",
     "resource_id": "<rag-tool-id>",
     "principal_type": "user",
     "principal_id": "<curator-user-id>",
     "access_level": "write"
   }
   ```

3. The curator's role (`kg-curator` in the seed fixtures)
   already grants `read:rag_tools` and `write:rag_tools`, so the
   grant takes effect immediately — they can now view and edit
   the tool but not delete or re-share it.
4. The audit log records both the grant creation and the
   subsequent edit events with the curator as actor.

## Where to go next

- [Overview](./overview) — the bigger picture.
- [Roles](./roles) — the capability ceiling.
- [Access log](./access-log) — verifying that the right grants
  exist and tracing who used them.
