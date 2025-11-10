#!/usr/bin/env sh
set -eu

# Make uvicorn honor proxy headers and the mount path
export UVICORN_CMD_ARGS="--proxy-headers --forwarded-allow-ips='*' --root-path /api"

# DB migrations
alembic upgrade head

# Gunicorn + UvicornWorker
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60