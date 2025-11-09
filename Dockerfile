# syntax=docker/dockerfile:1.7

# -------- base with system deps --------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Needed for psycopg2 and building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# -------- deps layer (cacheable) --------
FROM base AS deps
COPY requirements.txt .
# Make sure gunicorn is installed (either in requirements.txt or here)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn uvicorn

# -------- runtime (prod) --------
FROM deps AS prod
# Copy app source
COPY . .

# Optional: non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health endpoint expected at /ping
EXPOSE 8000

# Entrypoint script runs migrations then launches gunicorn
# (You already created start.sh. Keep it executable in repo.)
CMD ["/app/start.sh"]