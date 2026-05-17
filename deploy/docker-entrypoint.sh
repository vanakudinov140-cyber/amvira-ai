#!/bin/sh
set -e

cd /app

echo "[entrypoint] Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting FastAPI (127.0.0.1:8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' &
API_PID=$!

cleanup() {
  echo "[entrypoint] Shutting down..."
  kill "$API_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
}
trap cleanup TERM INT

echo "[entrypoint] Starting nginx (:80)..."
exec nginx -g 'daemon off;'
