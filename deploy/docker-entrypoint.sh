#!/bin/sh

cd /app

echo "[entrypoint] Running migrations..."
alembic upgrade head || true

echo "[entrypoint] Starting FastAPI..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*"
