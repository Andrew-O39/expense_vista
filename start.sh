#!/usr/bin/env sh
set -eu

# Let Uvicorn (inside Gunicorn) trust proxy headers from nginx/Caddy
# so it can correctly infer client IP, scheme (https), etc.
export PROXY_HEADERS=1
export FORWARDED_ALLOW_IPS="*"

# 1) Run DB migrations
alembic upgrade head

# 2) Start Gunicorn with Uvicorn workers
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60