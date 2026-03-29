FROM node:20-alpine AS deps

WORKDIR /workspace/apps/web

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci


FROM node:20-alpine AS builder

WORKDIR /workspace/apps/web

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api/v1
ARG NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8080/api/v1

ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_BASE_URL=$NEXT_PUBLIC_WS_BASE_URL

COPY --from=deps /workspace/apps/web/node_modules ./node_modules
COPY apps/web ./
COPY packages /workspace/packages
COPY tsconfig.base.json /workspace/tsconfig.base.json

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
