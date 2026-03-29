FROM node:20-alpine

WORKDIR /workspace/apps/web

COPY apps/web/package.json apps/web/package-lock.json* /workspace/apps/web/
RUN npm install

COPY apps/web /workspace/apps/web
COPY packages /workspace/packages
COPY tsconfig.base.json /workspace/tsconfig.base.json

CMD ["npm", "run", "dev"]
