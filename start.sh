#!/usr/bin/env sh
set -eu

# Allow proxied headers (Gunicorn understands this flag)
# (Caddy/Nginx set X-Forwarded-*, and this tells Gunicorn to trust them)
# You can keep these envs, but they're not required by Gunicorn:
export PROXY_HEADERS=1
export FORWARDED_ALLOW_IPS="*"

# 1) Run DB migrations
alembic upgrade head

# 2) Start the app via Gunicorn + Uvicorn workers
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --forwarded-allow-ips="*"