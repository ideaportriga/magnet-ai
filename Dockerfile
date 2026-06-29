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

# Stage 2: Build API dependencies using Poetry (Ubuntu 24.04 LTS — ships Python 3.12 natively)
FROM ubuntu:24.04 AS api-builder

ENV DEBIAN_FRONTEND=noninteractive \
    POETRY_HOME=/opt/poetry
ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /app

# Python 3.12 toolchain + build deps (this stage is discarded, so build tooling here is free)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-dev \
        build-essential ca-certificates \
    && python3 -m venv "${POETRY_HOME}" \
    && "${POETRY_HOME}/bin/pip" install --no-cache-dir poetry==1.8.3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY api/poetry.lock api/poetry.toml api/pyproject.toml ./

# Force the in-project .venv to use the system Python 3.12 (matches the final stage)
RUN poetry env use /usr/bin/python3 \
    && poetry install --no-interaction --no-root --only main

# Stage 3: Runtime image on Ubuntu 24.04 LTS (Python 3.12 native; far fewer OS CVEs than debian-slim)
FROM ubuntu:24.04 AS final

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3 \
        python-is-python3 \
        netcat-openbsd \
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
    && npm i -g @llamaindex/liteparse \
    && npm cache clean --force \
    # npm is only needed to install liteparse at build time; remove it (and its bundled undici) from the runtime image
    && rm -rf /usr/lib/node_modules/npm /usr/bin/npm /usr/bin/npx \
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

# Ubuntu 24.04 ships a default "ubuntu" user/group at uid/gid 1000 — remove it so we can reuse 1000 for app
RUN userdel --remove ubuntu 2>/dev/null || true \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app \
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