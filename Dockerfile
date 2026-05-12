# syntax=docker/dockerfile:1
# Amvera / root build: контекст — корень репозитория (папка Code). Код API — nestjs-api/.
# Локальная сборка из nestjs-api: используйте nestjs-api/Dockerfile и docker-compose в nestjs-api.
FROM node:22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache openssl

COPY nestjs-api/package.json nestjs-api/package-lock.json* ./
COPY nestjs-api/prisma ./prisma/

RUN npm ci

COPY nestjs-api/tsconfig.json nestjs-api/tsconfig.build.json nestjs-api/nest-cli.json ./
COPY nestjs-api/src ./src

RUN npx prisma generate
RUN npm run build

FROM node:22-alpine AS production

WORKDIR /app

ENV NODE_ENV=production

RUN apk add --no-cache openssl

COPY nestjs-api/package.json nestjs-api/package-lock.json* ./
COPY nestjs-api/prisma ./prisma/

RUN npm ci --omit=dev && npm cache clean --force \
  && npm install -g prisma@6.16.2

COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma/client ./node_modules/@prisma/client
COPY --from=builder /app/dist ./dist

COPY nestjs-api/scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 3000

USER node

ENTRYPOINT ["/app/docker-entrypoint.sh"]
