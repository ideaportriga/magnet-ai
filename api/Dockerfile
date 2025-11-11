# Stage 1: Build dependencies using Poetry
FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3


COPY poetry.lock poetry.toml pyproject.toml ./

RUN poetry install --no-interaction --no-root --only main

# Stage 2: Create a smaller image with just the application
FROM python:3.14-slim AS runner

WORKDIR /app

RUN mkdir files

# Copy only installed dependencies
COPY --from=builder /app/.venv ./.venv

COPY src ./src

ENV PYTHONPATH=/app/src

ENTRYPOINT [".venv/bin/uvicorn", "app:app", "--host", "0.0.0.0"]
