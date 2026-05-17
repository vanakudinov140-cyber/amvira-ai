# Production: admin-dashboard (static) + FastAPI + nginx — для Amvera и git deploy
# Порт контейнера: 80 (см. amvera.yml → containerPort: 80)

FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY admin-dashboard/package.json admin-dashboard/package-lock.json ./
RUN npm ci

COPY admin-dashboard/ ./

ARG VITE_API_URL=
ARG VITE_ENV_LABEL=Тестовый режим
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ENV_LABEL=$VITE_ENV_LABEL

RUN npm run build

# -----------------------------------------------------------------------------

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default \
    && sed -i 's|include /etc/nginx/sites-enabled/\*;|# include /etc/nginx/sites-enabled/*;|' /etc/nginx/nginx.conf \
    && mkdir -p /var/lib/nginx/body /var/lib/nginx/proxy /var/lib/nginx/fastcgi /var/lib/nginx/uwsgi /var/lib/nginx/scgi /run \
    && chown -R www-data:www-data /var/lib/nginx /usr/share/nginx/html

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/alembic.ini .
COPY backend/alembic ./alembic
COPY backend/app ./app

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html
COPY deploy/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh \
    && find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

EXPOSE 80

# Liveness: dashboard on :80 (не зависит от PostgreSQL)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -fsS http://127.0.0.1/ || exit 1

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/docker-entrypoint.sh"]
