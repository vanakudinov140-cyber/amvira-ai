#!/bin/sh
# Amvera: uvicorn PID 1, liveness /health без ожидания миграций

cd /app

echo "[entrypoint] Running migrations (background)..."
( alembic upgrade head || echo "[entrypoint] migrations failed or skipped" ) &

echo "[entrypoint] Starting FastAPI on 0.0.0.0:8000..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*"
