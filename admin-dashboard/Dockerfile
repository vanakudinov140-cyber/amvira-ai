FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Пустой URL = запросы на тот же origin (nginx проксирует /health, /analytics, …)
ARG VITE_API_URL=
ARG VITE_ENV_LABEL=Тестовый режим
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ENV_LABEL=$VITE_ENV_LABEL

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
