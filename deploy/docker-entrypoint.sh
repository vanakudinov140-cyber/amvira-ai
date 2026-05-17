#!/bin/sh
# Amvera: миграции до старта API; DATABASE_URL обязателен (не localhost)
set -e

cd /app

if [ -z "${DATABASE_URL:-}" ]; then
  echo "[entrypoint] FATAL: DATABASE_URL is not set."
  echo "[entrypoint] Amvera → PostgreSQL project → internal host (…-rw:5432)"
  echo "[entrypoint] Example:"
  echo "  postgresql+asyncpg://USER:PASS@amvera-USER-cnpg-PROJECT-rw:5432/DB_NAME"
  exit 1
fi

case "$DATABASE_URL" in
  *@localhost:*|*@localhost/*|*@127.0.0.1:*|*@127.0.0.1/*)
    if [ "${ALLOW_LOCAL_DB:-}" != "true" ]; then
      echo "[entrypoint] FATAL: DATABASE_URL points to localhost."
      echo "[entrypoint] Use Amvera internal PostgreSQL host (amvera-*-cnpg-*-rw)."
      exit 1
    fi
    ;;
esac

DB_HOST=$(printf '%s' "$DATABASE_URL" | sed -n 's/.*@\([^:/]*\).*/\1/p')
echo "[entrypoint] DATABASE_URL host: ${DB_HOST:-unknown}"
echo "[entrypoint] ENVIRONMENT: ${ENVIRONMENT:-development}"

echo "[entrypoint] Running alembic upgrade head..."
alembic upgrade head

echo "[entrypoint] Starting FastAPI on 0.0.0.0:8000..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*"
