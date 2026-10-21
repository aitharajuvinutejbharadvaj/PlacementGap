FROM node:22-alpine AS web-build
WORKDIR /app/web
RUN corepack enable
COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
COPY --from=web-build /app/web/dist /app/web/dist
EXPOSE 8000
CMD ["sh","-c","uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
