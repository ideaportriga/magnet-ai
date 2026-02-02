# DevOps Guide

Run Magnet AI in production: deployment patterns, environment configuration, and database operations.

## What you deploy

Most production setups consist of:

- **Magnet AI application**: one container image bundling the API + Admin UI + Panel UI + built-in Help docs
- **PostgreSQL + pgvector**: your primary application database
- **Ingress / reverse proxy**: TLS termination and routing (Kubernetes Ingress, OpenShift Route, Nginx, etc.)

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

- [Get Started](/docs/en/devops/get-started) - Quick path to get Magnet AI running quickly in a production-like setup.
- [Deployment Options](/docs/en/devops/deployment/) - Different options for Magnet AI deployment.