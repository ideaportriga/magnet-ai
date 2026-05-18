# Access control (RBAC) — overview

Magnet AI uses a **role-based access control** model with record-level
overrides. Every API call and every UI panel asks the same question:
*can this principal perform this action on this resource?* The answer
combines four things:

1. **Authentication** — who is the user (or API key) and which tenant
   do they belong to?
2. **Role membership** — which roles are assigned to that user?
3. **Permission catalog** — what global capabilities (`read:agents`,
   `write:rag_tools`, …) does each role hold?
4. **Record-level rules** — for a specific record, do its
   *visibility*, *owner*, or *explicit grants* let this user act?

The first three define the **capability ceiling**: even a record-level
grant can't elevate a user past what their role allows. The fourth
narrows visibility within that ceiling so a tenant-level "read:agents"
permission, for example, doesn't expose every agent in the tenant.

::: tip
If you administer the system day-to-day, jump to
[Managing users](./users) and [Managing roles](./roles).
For the full permission catalog see the
[Permissions reference](./permissions-reference).
:::

## Core concepts

### Tenants

A **tenant** is the top-level isolation boundary — in single-org
deployments it is the organization itself. Every user, role, agent,
RAG tool, document, and access grant belongs to exactly one tenant.
Row-level security in PostgreSQL prevents cross-tenant reads even if
application code forgets to filter.

### Users

A user has:

- A persistent identity (email, name, `is_active`, `is_superuser`).
- One **home tenant** (set on creation, immutable through the UI).
- Zero or more **roles** within that tenant.
- Optional membership in **departments** (with `is_lead` flag) and
  **groups**.

There is also a **superuser** flag (`is_superuser=true`) which
short-circuits every check — superusers see and modify everything in
every tenant. Use this only for the bootstrap account and platform
operators.

### Roles

Roles bundle permissions and are assigned to users. Two flavours
exist:

| Type | `is_system` | `tenant_id` | Mutable? | Created by |
|---|---|---|---|---|
| **System role** | `true` | `NULL` | No | Database migration |
| **Custom role** | `false` | a tenant | Yes | Admin UI |

Three system roles ship out of the box:

- **admin** — every permission. Tenant administrators.
- **user** — read + execute on most resources, write on files and
  the Note Taker. The "regular employee" profile.
- **viewer** — read-only across the board.

System roles cannot be edited. Need a different shape? Clone one as a
custom role and tailor its permission set.

### Permissions

Every permission is a `verb:resource` string, e.g. `read:agents`,
`write:rag_tools`, `manage:users`. Permissions are seeded into the
`permission` table by migration; the canonical list lives in the
`Permission` enum on the API
(`api/src/guards/permissions.py`).

Common verbs:

- **read** — list and view detail pages.
- **write** — create and edit.
- **delete** — remove.
- **execute** — run an agent or other executable resource.
- **share** — change visibility or grant access to others.
- **manage** — administrative super-verb (used for users and
  resource-access grants).

See the [permission reference](./permissions-reference) for the full
catalog grouped by resource.

### Record-level access

Roles alone control coarse, tenant-wide capability. To answer
"who can see *this specific agent*?", three more inputs come in:

- **`visibility`** on the record — `private` / `department` /
  `tenant`. Tenant visibility means anyone in the tenant with the
  matching read capability can see it.
- **`owner_id`** — the creator (or a transferred owner). Owners
  always retain the actions their role permits on records they own.
- **Resource access grants** — explicit `read` / `write` / `admin`
  grants on a single record to a **user**, **group**, or
  **department**. Grants only **narrow** the capability ceiling;
  they can never grant a permission the principal's roles don't
  already imply.

When a user has zero matching grants and the record is `private` and
not owned by them, the record is **invisible** — both list queries
and direct `GET /by-id` return 404.

### Departments and groups

- **Departments** model the org chart (e.g. *Marketing*,
  *Engineering*). A user can belong to several. Department membership
  drives `visibility=department` records and is also a principal type
  for resource-access grants.
- **Groups** are flat, ad-hoc sets of users (e.g. *KG Curators*,
  *Beta testers*). They are not in the org chart and exist only to
  receive access grants.

### Access audit log

Every RBAC mutation — role created/edited/deleted, user assigned a
role, resource grant added or revoked — is written to the
**access audit log** with the actor, target principal, action, and
diff. It is append-only and visible in the admin UI at
**System → Access log**.

See [Access log](./access-log).

## How a decision is made

When the API receives a request, the algorithm is:

1. Authenticate. If anonymous, deny (some public endpoints are
   exempted explicitly).
2. Resolve the principal's **tenant** and **effective permission
   set**. For password / JWT users this is the union of permissions
   across their roles. For API keys it is the key's `scopes` (no
   role union — keys cannot exceed their declared scope).
3. Reject if the required capability (e.g. `write:agents`) is
   missing.
4. For list endpoints, append a SQL filter that selects only rows
   the principal owns, has department/tenant visibility for, or
   holds a grant on.
5. For single-record endpoints, run the same logic on the loaded
   row. A cross-tenant record returns 404; an in-tenant record the
   user is not entitled to also returns 404 to avoid leaking
   existence.

Tenant admins (system `admin` role within their tenant) and
superusers short-circuit step 4 and 5 — they see every record in
their tenant (admins) or every tenant (superusers).

## Where to go next

- [Managing users](./users) — create, deactivate, assign roles.
- [Managing roles](./roles) — clone, edit the permission matrix.
- [Permissions reference](./permissions-reference) — the full
  catalog.
- [Access log](./access-log) — auditing changes.
