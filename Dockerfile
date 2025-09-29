# syntax=docker/dockerfile:1.7

### ---- Base image with system deps ----
ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps (Postgres client headers, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

### ---- Install Python deps ----
# Keep requirements.txt at repo root
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

### ---- Copy application code ----
# Copy the whole project (including alembic.ini and alembic/ at repo root)
COPY . /app

# Non-root user for safety
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Common runtime env
ENV PORT=8000 \
    UVICORN_WORKERS=2 \
    PYTHONPATH=/app \
    ALEMBIC_CONFIG=/app/alembic.ini

EXPOSE 8000

# Healthcheck hits your /ping (or /health) endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/ping || exit 1

### ---- Production default command ----
# Runs DB migrations and then starts Gunicorn+Uvicorn workers
CMD ["sh","-c","alembic upgrade head && exec gunicorn -k uvicorn.workers.UvicornWorker -w ${UVICORN_WORKERS} -b 0.0.0.0:${PORT} main:app"]

### ---- Optional Dev target (hot reload) ----
FROM base AS dev
CMD ["sh","-c","alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"]