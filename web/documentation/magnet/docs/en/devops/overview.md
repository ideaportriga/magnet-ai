# DevOps Guide

Run Magnet AI in production: deployment patterns, environment configuration, and database operations.

## What you deploy

Most production setups consist of:

- **Magnet AI application**: one container image bundling the API
  + Admin UI + Panel UI + built-in Help docs. The same image runs
  the **Taskiq worker** and **scheduler** as in-process asyncio
  tasks by default — see [Background tasks](./taskiq) for the
  multi-process layout.
- **PostgreSQL + pgvector**: primary application database; doubles
  as the Taskiq broker out of the box — no separate Redis /
  RabbitMQ required.
- **Ingress / reverse proxy**: TLS termination and routing
  (Kubernetes Ingress, OpenShift Route, Nginx, etc.).

Key paths:

- **Admin UI**: `/admin/`
- **Panel UI**: `/panel/`
- **Help docs**: `/help/`
- **API**: `/api/`
- **Health check**: `/health`

## Core operational concepts

- **Configuration**: Magnet AI reads most settings from environment variables.
- **Secrets**: store secrets in your platform secret manager and keep `SECRET_ENCRYPTION_KEY` stable across restarts (it encrypts/decrypts secrets stored in the database).
- **Database lifecycle**: use Alembic migrations for schema changes.

## Where to go next

- [Get Started](/docs/en/devops/get-started) — Quick path to get
  Magnet AI running in a production-like setup.
- [Deployment Options](/docs/en/devops/deployment/) — Different
  options for Magnet AI deployment.
- [Background tasks (Taskiq)](/docs/en/devops/taskiq) — Worker
  and scheduler topology, tuning, and migration from APScheduler.