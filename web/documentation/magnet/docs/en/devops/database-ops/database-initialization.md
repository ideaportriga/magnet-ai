# Database Initialization (first run)

Initialize a fresh PostgreSQL database for Magnet AI.

## Prerequisites

- PostgreSQL (supported version per your platform)

## 1. Create database and user (if needed)

If your PostgreSQL platform does not pre-provision a database/user for you, create them first (adjust names/passwords to your standards):

```sql
-- Run as an admin user (or the platform-provided superuser)
CREATE ROLE magnet WITH LOGIN PASSWORD 'strong-password-here';
CREATE DATABASE magnet_prod OWNER magnet;
```

> If you’re using a managed PostgreSQL service, you may need to use the provider’s UI/CLI to create the database/user, or reuse the admin user.

## 2. Apply schema migrations

Magnet AI uses **Alembic** migrations.

### Option A: run migrations during deploy (recommended for containers)

Set `RUN_MIGRATIONS=true` in your deployment (Docker Compose / Kubernetes / Azure examples do this). On startup, the container will apply migrations automatically.

### Option B: run migrations from the repo

From the repo root (requires `npm` + `poetry` configured):

```bash
npm run db:upgrade
```

## 3. (Optional) Load fixtures

Fixtures can be useful for development/testing. For production environments, only load fixtures if you know you need them.

From the repo root:

```bash
npm run fixtures:load
```
