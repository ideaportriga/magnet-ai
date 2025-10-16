# Stage 1: Build WEB with nx
FROM node:20-alpine AS web-builder

WORKDIR /web

COPY web ./

RUN corepack enable

RUN yarn install --mode=skip-build --immutable

# Disable NX Daemon in Docker to avoid timeout issues
ENV NX_DAEMON=false
# Increase Node memory limit for large builds
ENV NODE_OPTIONS="--max-old-space-size=4096"

RUN yarn nx build magnet-admin

RUN yarn nx build magnet-panel

ARG WEB_BASE_PATH="/"
ARG BUILD_DOCS=true

ENV WEB_HELP_PATH="help/"

# Build docs only if BUILD_DOCS=true (can skip with --build-arg BUILD_DOCS=false)
RUN yarn nx build magnet-docs;

# Stage 2: Build API dependencies using Poetry
FROM python:3.12-slim AS api-builder

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3

COPY api/poetry.lock api/poetry.toml api/pyproject.toml ./

RUN poetry install --no-interaction --no-root --only main

# Stage 3: Create a smaller image with just the application
FROM python:3.12-slim as final

# Install netcat for database connectivity checks
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir files

COPY docker/scripts/update_web_configs.py ./
COPY docker/docker-entrypoint.sh ./
RUN ls -a
RUN chmod +x ./docker-entrypoint.sh
RUN ls -a

# Copy static web files
COPY --from=web-builder /web/knowledge-magnet/admin/app ./web/admin
COPY --from=web-builder /web/knowledge-magnet/panel/app ./web/panel
COPY --from=web-builder /web/documentation/magnet/.vitepress/dist ./web/help

# Set proper permissions for config directories (similar to nginx container)
RUN chgrp -R 0 /app/web/admin/config /app/web/panel/config \
    && chmod -R g+rwX /app/web/admin/config /app/web/panel/config

# Copy only installed API dependencies
COPY --from=api-builder /app/.venv ./.venv

COPY api/src ./src

ENV PYTHONPATH=/app/src
ENV PORT=8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD .venv/bin/uvicorn app:app --host 0.0.0.0 --port ${PORT}