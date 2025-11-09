# syntax=docker/dockerfile:1.7

# -------- base with system deps --------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# -------- deps layer --------
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn uvicorn

# -------- dev stage (hot reload) --------
FROM deps AS dev
WORKDIR /app
COPY . .
# optional non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--reload"]

# -------- prod stage --------
FROM deps AS prod
WORKDIR /app
COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["/app/start.sh"]   # your start.sh runs alembic + gunicorn