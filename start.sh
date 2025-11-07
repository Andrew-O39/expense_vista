#!/usr/bin/env bash
set -e
alembic upgrade head
exec gunicorn main:app \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 60
