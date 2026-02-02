# Deployment

Deploy Magnet AI to your environment. The guides below cover production-oriented setups and the operational concerns you’ll need to address (database, secrets, TLS/routing, and upgrades).

**Container image**: Magnet AI is published as a prebuilt container image: `ghcr.io/ideaportriga/magnet-ai:latest`.

## Deployment options

- [Docker Compose](/docs/en/devops/deployment/docker-compose/) - Deploy Magnet AI in a production-like, single-host setup using Docker Compose (PostgreSQL + pgvector + Nginx reverse proxy).
- [Kubernetes/OpenShift](/docs/en/devops/deployment/kubernetes/) - Deploy Magnet AI to Kubernetes or OpenShift by running the Magnet AI container image and connecting it to a PostgreSQL database with `pgvector` enabled.
- [Azure](/docs/en/devops/deployment/cloud/azure) - Deploy Magnet AI on Azure using Azure Container Apps and Azure Database for PostgreSQL.

## Database (required)

All deployment options require **PostgreSQL with `pgvector` enabled**.

- **Docker Compose**: includes a PostgreSQL + pgvector service in the stack (good for self-hosted single-host deployments). For higher availability, replace it with a managed PostgreSQL service and point `DB_*` variables to it.
- **Kubernetes/OpenShift**: this guide assumes you already have a PostgreSQL endpoint (managed DB or operator). Database installation is intentionally **out of scope** for the Kubernetes guide.
- **Azure**: the Azure guide includes provisioning **Azure Database for PostgreSQL** and enabling `pgvector`.

For initializing the database follow [Database Initialization](/docs/en/devops/database-ops/database-initialization) guide.

## Minimum production checklist

- **Secrets**: store secrets in your platform secret manager; keep `SECRET_ENCRYPTION_KEY` stable across restarts.
- **Routing/TLS**: route `/admin/`, `/panel/`, `/help/`, `/api/` and terminate TLS.
- **Migrations**: run Alembic migrations during deploy (containerized deployments typically set `RUN_MIGRATIONS=true`).