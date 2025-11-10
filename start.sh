#!/usr/bin/env bash
set -euo pipefail

# Run DB migrations first (using alembic.ini in the repo)
alembic upgrade head

# Start app with Gunicorn + Uvicorn workers
# Adjust workers based on instance size (2 is fine for t2.micro-like)
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60