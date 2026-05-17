#!/bin/sh
# Production entrypoint (Amvera): nginx on :80 (PID 1 via tini), API on 127.0.0.1:8000

cd /app

API_PID=""
MIG_PID=""

cleanup() {
  echo "[entrypoint] Shutting down..."
  if [ -n "$API_PID" ]; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
  if [ -n "$MIG_PID" ]; then
    kill "$MIG_PID" 2>/dev/null || true
    wait "$MIG_PID" 2>/dev/null || true
  fi
  nginx -s quit 2>/dev/null || true
}
trap cleanup TERM INT

run_migrations() {
  echo "[entrypoint] Alembic migrations (background, with retries)..."
  TRIES=30
  n=0
  while [ "$n" -lt "$TRIES" ]; do
    if alembic upgrade head; then
      echo "[entrypoint] Migrations complete"
      return 0
    fi
    n=$((n + 1))
    if [ "$n" -lt "$TRIES" ]; then
      echo "[entrypoint] migration attempt ${n}/${TRIES} failed, retry in 5s..."
      sleep 5
    fi
  done
  echo "[entrypoint] WARNING: migrations incomplete — check DATABASE_URL and PostgreSQL"
  return 1
}

nginx -t || exit 1

run_migrations &
MIG_PID=$!

echo "[entrypoint] Starting FastAPI (127.0.0.1:8000)..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips='*' &
API_PID=$!

echo "[entrypoint] Starting nginx on 0.0.0.0:80 (foreground)..."
exec nginx -g 'daemon off;'
