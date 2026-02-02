# Run with Docker Compose

This page explains how to run **Magnet AI locally** using the repository’s root `docker-compose.yml` (includes **PostgreSQL + pgvector**).

For production deployment guidance, use the **DevOps Guide**:

- `/docs/en/devops/deployment/docker-compose/`
- `/docs/en/devops/deployment/kubernetes/`

## Prerequisites

- Docker Desktop / Docker Engine
- Docker Compose v2 (`docker compose`)
- 4GB+ RAM (more recommended for first build)

## Quick start

From the repository root:

```bash
# 1) Create a root .env file (see example below)
# 2) Build + start services
docker compose up -d --build
```

When it’s up, you can access:

- **User Panel**: `http://localhost:5000/panel/`
- **Admin Console**: `http://localhost:5000/admin/`
- **API health**: `http://localhost:5000/health`
- **Help/Docs (offline)**: `http://localhost:5000/help/`

## Environment configuration

`docker-compose.yml` loads variables from a root `.env` file.

Create `.env` in the repository root:

```bash
# Required for AI features
OPENAI_API_KEY=sk-...

# App port (host -> container). Default: 5000
PORT=5000

# Postgres (host port is exposed as DB_PORT; container uses 5432 internally)
DB_NAME=magnet_dev
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5433

# Local convenience (recommended)
AUTH_ENABLED=false
```

Notes:

- The database is exposed on your machine as `localhost:${DB_PORT}` (default `5433`).
- The app container connects to Postgres via the Docker network (`DB_HOST=postgres`, `DB_PORT=5432` inside the network).

## What Docker Compose runs

The root `docker-compose.yml` starts:

- **`postgres`**: `pgvector/pgvector:pg16` with an init script that enables `pgvector`
- **`app`**: the Magnet AI API (Litestar) plus bundled static web apps (served from the same container)

On container start, Magnet automatically:

- waits for Postgres
- applies DB migrations (unless disabled)

## Common commands

### Stop / start

```bash
docker compose up -d
docker compose down
```

### View logs

```bash
docker compose logs -f app
docker compose logs -f postgres
```

### Rebuild the app image

```bash
docker compose build app
docker compose up -d --force-recreate app
```

### Faster builds (skip docs build)

The Docker image can optionally skip building the documentation for faster iteration.

In your `.env`:

```bash
BUILD_DOCS=false
```

Then rebuild:

```bash
docker compose build app
docker compose up -d --force-recreate app
```

## Database access (from your host)

To connect from your machine (e.g., DBeaver), use:

- **Host**: `localhost`
- **Port**: `${DB_PORT}` (default `5433`)
- **Database**: `${DB_NAME}` (default `magnet_dev`)
- **User**: `${DB_USER}` (default `postgres`)
- **Password**: `${DB_PASSWORD}` (default `password`)

## Resetting the database (danger)

The container supports a destructive reset mode that **drops all tables** and reapplies migrations.

1. Set this in `.env` temporarily:

```bash
RESET_DB=true
```

2. Recreate the `app` container so it picks up the updated env var:

```bash
docker compose up -d --force-recreate app
```

3. Set `RESET_DB=false` again and recreate the `app` container once more.

## Next steps

- [Local Development](/docs/en/developers/setup/local-development) - Hot reload / contributor workflow
- [Testing](/docs/en/developers/setup/testing) - Running test suites
- [DevOps Guide](/docs/en/devops/overview) - Production deployment & operations
