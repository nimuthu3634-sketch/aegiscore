FROM node:20-alpine

WORKDIR /workspace/frontend

COPY frontend/package.json ./
COPY frontend/tsconfig.json ./
COPY frontend/tsconfig.app.json ./
COPY frontend/tsconfig.node.json ./
COPY frontend/tailwind.config.cjs ./
COPY frontend/postcss.config.cjs ./
COPY frontend/vite.config.ts ./
COPY frontend/index.html ./
COPY frontend/public ./public
COPY frontend/src ./src
COPY assets ../assets

RUN npm install

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
