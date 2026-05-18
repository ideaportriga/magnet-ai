# Stage 1: Build dependencies using uv
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Create a smaller image with just the application
FROM python:3.13-slim AS runner

WORKDIR /app

RUN mkdir files

# Copy only installed dependencies
COPY --from=builder /app/.venv ./.venv

COPY src ./src

ENV PYTHONPATH=/app/src

ENTRYPOINT [".venv/bin/uvicorn", "app:app", "--host", "0.0.0.0"]
