# What's new in the alpha release

The alpha line is the next major version of Magnet AI. This page is
a digest of the headline changes versus the previous `develop`
branch — intended as a launching pad into the per-feature docs.

## 🔐 Role-based access control

A complete authorization model:

- **Roles** — three built-in (`admin`, `user`, `viewer`) plus
  custom tenant-scoped roles you create from the permission matrix.
- **Permissions** — `verb:resource` codes for every API operation,
  enforced as both route guards (capability ceiling) and
  per-record checks (visibility / owner / explicit grants).
- **Departments and groups** — model the org chart and ad-hoc sets
  of users; both work as principal types for resource-access
  grants.
- **Access audit log** — append-only trail of every governance
  mutation, with diffs and request trace IDs.

→ See [Admin → Access control](./admin/access/overview).

## 🔑 Authentication v2

The login stack was rebuilt:

- **Local email/password** with Argon2 hashing.
- **OAuth 2 / OIDC** providers (Google, GitHub) for SSO.
- **MFA / TOTP** with backup codes.
- **Refresh tokens** with family-based reuse detection.
- **Email verification** and password reset flows.
- **OAuth client tables** so external apps (e.g. Claude via MCP)
  can authenticate against Magnet via standard OAuth 2.1.

## 🧠 Embedded MCP server

Magnet exposes its own MCP (Model Context Protocol) server so
Claude Desktop or any MCP client can call back into the platform:

- Tools for evaluations, LLM monitoring, prompt execution and
  prompt templates.
- OAuth 2.1 authentication; DNS rebinding protection.

Enable with `MCP_ENABLED=true`; see `.env.example` for the full set
of `MCP_*` variables.

## 🎙 Note Taker

A new resource type for meeting transcripts and recordings, fed by
a hardened **Microsoft Teams webhook → STT → integrations**
pipeline. Reliability features:

- Durable retries via taskiq's `schedule_by_time`.
- Cron-driven housekeeping of webhook events.
- Observable `notetaker.running_jobs` gauge.

## ⚙️ Taskiq replaces APScheduler

The background-task engine is now **taskiq**. Two flavours:

- **In-process** workers and scheduler (default; ideal for local
  dev and single-container deploys). Toggled with
  `TASKIQ_INPROCESS_WORKER_ENABLED` and
  `TASKIQ_INPROCESS_SCHEDULER_ENABLED`.
- **CLI** worker and scheduler — what `npm run dev:worker` and
  `npm run dev:scheduler` invoke.

APScheduler is gone from the alpha; if you are coming from develop,
expect new env vars and one-time migration `2026-04-21_taskiq_migration`.

## 🧪 RAG redesign

The RAG section was rewritten end-to-end:

- Separate **Retrieve**, **Generate**, **Test sets** and **Answer
  evaluation** tabs in the RAG tool detail page.
- New Retrieval tools page (search-only configurations).
- Distributed-tracing spans for the full RAG pipeline
  (ChatCompletion, Embed, Search, Fuse, Rerank) on the
  Observability → Traces page.

## 📚 Knowledge graph

Expanded into Content profiles, Entity extraction, Metadata
management, and a Data explorer for browsing extracted entities
and source documents.

## 🎨 New design system

UI was migrated from PrimeVue to **Reka UI + CUBE CSS** with a
Magnet design-system layer (`@ds` / `Km*` components). Every
admin page is rebuilt around the new primitives — sidebar
sections, list pages, drawer details, etc.

→ See [Frontend architecture](./developers/architecture/frontend).

## 🛠 New dev / ops scripts

- `npm run setup:fresh` — docker up → db create → migrate →
  bootstrap superuser, in one command.
- `npm run bootstrap:superuser` — idempotent superuser creation
  from `BOOTSTRAP_SUPERUSER_*` env vars.
- `api/scripts/seed_dev_fixtures.py` — creates the `super@`,
  `admin@`, `user@`, `viewer@`, `curator@` test users plus
  departments and sample agents (used by Cypress e2e).
- New Makefile targets for fresh-deploy and test orchestration.

→ See [Developer Setup → Getting Started](./developers/setup/getting-started).
