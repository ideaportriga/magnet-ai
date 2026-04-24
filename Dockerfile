# Stage 1: Build WEB with nx
FROM node:24.15.0-alpine AS web-builder

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
FROM python:3.12-slim AS final

RUN apt-get update && apt-get install -y --no-install-recommends \
        netcat-traditional \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-deu \
        tesseract-ocr-fra \
        tesseract-ocr-rus \
        ca-certificates \
        curl \
        gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm i -g npm@latest \
    && npm i -g @llamaindex/liteparse \
    && npm cache clean --force \
    && apt-get purge -y curl gnupg \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /root/.npm /tmp/*

WORKDIR /app

COPY docker/scripts/update_web_configs.py ./
COPY docker/docker-entrypoint.sh ./

COPY --from=web-builder /web/knowledge-magnet/admin/app ./web/admin
COPY --from=web-builder /web/knowledge-magnet/panel/app ./web/panel
COPY --from=web-builder /web/documentation/magnet/.vitepress/dist ./web/help

COPY --from=api-builder /app/.venv ./.venv

COPY api/src ./src
COPY api/scripts ./scripts
COPY api/static ./static
COPY api/manage_fixtures.py ./manage_fixtures.py

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --shell /sbin/nologin app \
    && mkdir -p /app/files \
    && chmod +x ./docker-entrypoint.sh \
    && chown -R app:app /app \
    && chgrp -R 0 /app/web/admin/config /app/web/panel/config \
    && chmod -R ug+rwX /app/web/admin/config /app/web/panel/config

USER app

ENV PYTHONPATH=/app/src \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD nc -z 127.0.0.1 "${PORT:-8000}" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["sh", "-c", ".venv/bin/uvicorn app:app --host 0.0.0.0 --port ${PORT}"]