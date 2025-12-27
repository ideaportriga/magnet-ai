# Get Started

Get Magnet AI running in a production-like setup using the published container image:

- `ghcr.io/ideaportriga/magnet-ai:latest`

This page is a quick guide; for full, production-oriented setups see the [Deployment Options](/docs/en/devops/deployment/) section.

## What you need

- **PostgreSQL with `pgvector` enabled** (required)
- **A place to run the container**:
  - single host: Docker Compose
  - cluster: Kubernetes/OpenShift
  - cloud: Azure Container Apps
- **A stable `SECRET_ENCRYPTION_KEY`** (do not rotate casually; it encrypts secrets stored in the database)

## Pick a deployment path

- **Docker Compose (fastest single-host path)**: [Docker Compose deployment](/docs/en/devops/deployment/docker-compose/)
- **Kubernetes/OpenShift**: [Kubernetes/OpenShift deployment](/docs/en/devops/deployment/kubernetes/)
- **Azure**: [Azure deployment](/docs/en/devops/deployment/cloud/azure)

## Fastest path: Docker Compose (recommended for single host)

If you’re deploying to a single VM/host, the Docker Compose guide is the quickest way to get a production-like stack running (PostgreSQL + pgvector, Magnet AI container `ghcr.io/ideaportriga/magnet-ai:latest`, and optional Nginx/TLS):

- [Docker Compose deployment](/docs/en/devops/deployment/docker-compose/)

## Minimum required configuration

Magnet AI is configured via environment variables. At minimum, provide:

- **Database**: `DB_TYPE=postgresql`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Secrets**: `SECRET_ENCRYPTION_KEY`
- **Runtime**: `ENV=production`, `PORT=5000`, `WEB_INCLUDED=true`
- **Migrations**: `RUN_MIGRATIONS=true` (recommended for container deployments)
- **Auth / CORS** (typical):
  - `AUTH_ENABLED=true` (recommended for production; for quick evaluation you can keep it `false`)
  - `CORS_OVERRIDE_ALLOWED_ORIGINS=https://yourdomain.com` (leave empty if the UI is served from the same origin)

## Validate your deployment

After deployment, verify:

- **Health**: `GET /health`
- **UI routes**:
  - `/admin/`
  - `/panel/`
  - `/help/`
- **API**: `/api/`

If the app can’t start, check logs first for:

- database connectivity / credentials
- missing `SECRET_ENCRYPTION_KEY`
- migrations failing (when `RUN_MIGRATIONS=true`)

## Next steps

- **Deployment details**: [Deployment Options](/docs/en/devops/deployment/)
- **First-time database setup**: [Database Initialization](/docs/en/devops/database-ops/database-initialization)