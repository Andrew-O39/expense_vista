#!/usr/bin/env sh
set -eu

# Make Uvicorn (the Gunicorn worker) trust proxy headers coming from nginx
# and correctly infer scheme = https and root_path = /api.
# These env vars are respected by uvicorn's Gunicorn worker.
export PROXY_HEADERS=1
export FORWARDED_ALLOW_IPS="*"

# Run DB migrations
alembic upgrade head

# Start Gunicorn + Uvicorn workers
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60