FROM node:20-alpine AS deps

WORKDIR /workspace/apps/web

COPY package.json package-lock.json* ./
RUN npm ci --fetch-retries=5 --fetch-retry-factor=2 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000


FROM node:20-alpine AS builder

WORKDIR /workspace/apps/web

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1
ARG NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8080/api/v1

ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_BASE_URL=$NEXT_PUBLIC_WS_BASE_URL

COPY --from=deps /workspace/apps/web/node_modules ./node_modules
COPY . ./

RUN npm run build


FROM node:20-alpine AS runner

ENV NODE_ENV=production
WORKDIR /workspace/apps/web

COPY --from=builder /workspace/apps/web ./

RUN addgroup -S aegis && adduser -S aegis -G aegis \
    && chown -R aegis:aegis /workspace

USER aegis

EXPOSE 3000

CMD ["npm", "run", "start"]
