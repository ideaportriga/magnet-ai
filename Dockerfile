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

# Stage 2: Build API dependencies using uv
FROM python:3.12-slim AS api-builder

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY api/pyproject.toml api/uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

# Stage 3: Create a smaller image with just the application
FROM python:3.12-slim as final

# Install netcat for database connectivity checks, ffmpeg, and Tesseract OCR
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

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
COPY api/scripts ./scripts
COPY api/static ./static

ENV PYTHONPATH=/app/src
ENV PORT=8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD .venv/bin/uvicorn app:app --host 0.0.0.0 --port ${PORT}