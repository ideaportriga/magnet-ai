# Docker Compose Deployment

Deploy Magnet AI in a production-like, single-host setup using Docker Compose (PostgreSQL + pgvector + Nginx reverse proxy).

## Prerequisites

- Docker 20.10+
- Docker Compose v2 (`docker compose`)
- 4GB+ RAM
- 20GB+ disk space

## Overview

- **Public entrypoint**: `nginx` (ports 80/443)
- **Application**: `app` (internal port 5000, serves Admin/Panel/Help + `/api`)
- **Database**: `postgres` (internal, persisted via a named volume)

## 1. Create a deployment directory

```bash
mkdir magnet-ai-deploy
cd magnet-ai-deploy
```

> This guide uses the prebuilt image `ghcr.io/ideaportriga/magnet-ai:latest`.

## 2. Environment configuration (`.env`)

This file serves two purposes:

- **Docker Compose variable substitution**: the compose file uses `${...}` values from `.env`.
- **Runtime configuration**: the same values are passed into the Magnet AI container as environment variables.

Create `.env` next to your `docker-compose.prod.yml`:

```bash
# Database (used by both Postgres and Magnet AI)
DB_NAME=magnet_prod
DB_USER=magnet
DB_PASSWORD=strong-password-here

# Encrypt/decrypt secrets stored in the database (provider keys, OAuth secrets, etc.)
# Keep this stable across restarts.
SECRET_ENCRYPTION_KEY=generate-strong-secret-key

# Auth / CORS
AUTH_ENABLED=true
# Leave empty when serving UI from the same domain; otherwise set explicitly.
CORS_OVERRIDE_ALLOWED_ORIGINS=https://yourdomain.com
```

## 3. Create Docker Compose file

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${DB_NAME:-magnet_prod}
      POSTGRES_USER: ${DB_USER:-magnet}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-magnet} -d ${DB_NAME:-magnet_prod}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  app:
    image: ghcr.io/ideaportriga/magnet-ai:latest
    environment:
      ENV: production
      PORT: 5000

      DB_TYPE: postgresql
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: ${DB_NAME:-magnet_prod}
      DB_USER: ${DB_USER:-magnet}
      DB_PASSWORD: ${DB_PASSWORD}

      WEB_INCLUDED: "true"
      AUTH_ENABLED: ${AUTH_ENABLED:-true}
      CORS_OVERRIDE_ALLOWED_ORIGINS: ${CORS_OVERRIDE_ALLOWED_ORIGINS:-https://yourdomain.com}

      RUN_MIGRATIONS: "true"

      # Encrypt/decrypt secrets stored in the database (provider keys, OAuth secrets, etc.)
      SECRET_ENCRYPTION_KEY: ${SECRET_ENCRYPTION_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: always

volumes:
  postgres_data:
```

## 4. Configure TLS + Nginx

### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get update
sudo apt-get install -y certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/
#
# Copy the certificate files to ./ssl for the nginx container:
# - fullchain.pem
# - privkey.pem
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 5. Deploy

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

After deploy, open:

- `https://yourdomain.com/admin/`
- `https://yourdomain.com/panel/`
- `https://yourdomain.com/help/`
- `https://yourdomain.com/api`

## 6. Upgrades

For updates, pull the latest image and restart:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```