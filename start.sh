#!/usr/bin/env sh
set -eu

# Make uvicorn/gunicorn trust proxy headers coming from the reverse proxy
# (Caddy/Nginx set X-Forwarded-*; we allow all since traffic is internal)
export PROXY_HEADERS=1
export FORWARDED_ALLOW_IPS="*"

# 1) Run DB migrations (alembic.ini in the repo)
alembic upgrade head

# 2) Start the app via Gunicorn + Uvicorn workers
#    --forwarded-allow-ips lets Gunicorn honor X-Forwarded-* from our proxy
exec gunicorn main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --forwarded-allow-ips="*" \
  --proxy-headers