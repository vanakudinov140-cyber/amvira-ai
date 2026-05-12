#!/bin/sh
set -e
echo "[entrypoint] prisma migrate deploy"
prisma migrate deploy
echo "[entrypoint] starting api"
exec node dist/main.js
