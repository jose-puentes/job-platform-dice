FROM node:22-alpine

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY apps/web ./

RUN npm run build

CMD ["npm", "run", "start"]

