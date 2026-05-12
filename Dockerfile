FROM node:20-alpine

WORKDIR /app

COPY nestjs-api/package*.json ./

RUN npm install

COPY nestjs-api .

RUN npx prisma generate

RUN npm run build

EXPOSE 3000

CMD ["node", "dist/main.js"]