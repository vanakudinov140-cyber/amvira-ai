# syntax=docker/dockerfile:1
# Рантайм: см. docs/AMVERA-DEPLOY.md (PORT, DATABASE_URL, REDIS_*, Prisma migrate в entrypoint).
FROM node:22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache openssl

COPY package.json package-lock.json* ./
COPY prisma ./prisma/

RUN npm ci

COPY tsconfig.json tsconfig.build.json nest-cli.json ./
COPY src ./src

RUN npx prisma generate
RUN npm run build

FROM node:22-alpine AS production

WORKDIR /app

ENV NODE_ENV=production

RUN apk add --no-cache openssl

COPY package.json package-lock.json* ./
COPY prisma ./prisma/

RUN npm ci --omit=dev && npm cache clean --force \
  && npm install -g prisma@6.16.2

COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma/client ./node_modules/@prisma/client
COPY --from=builder /app/dist ./dist

COPY scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 3000

USER node

ENTRYPOINT ["/app/docker-entrypoint.sh"]
