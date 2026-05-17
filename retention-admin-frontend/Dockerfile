# Retention Admin Dashboard — standalone SPA (nginx)
# Репозиторий: retention-admin-frontend (корень, без monorepo)
# API: https://retention-v2-ivankudinov.amvera.io

FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=https://retention-v2-ivankudinov.amvera.io
ARG VITE_ENV_LABEL=Production
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ENV_LABEL=$VITE_ENV_LABEL

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ || exit 1
