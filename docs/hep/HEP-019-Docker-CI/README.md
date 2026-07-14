# Docker & CI Configuration

## Docker Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  hermes-app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## CI Workflow (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install
      - run: pnpm -r exec tsc --noEmit
      - run: pnpm -r exec vitest run
      - run: pnpm -r exec tsc --outDir dist

  docker-build:
    needs: build-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t hermes-agent-os .
```

## Environment Variables

See `env/.env.example` for all required environment variables.

```
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
NODE_ENV=development
PORT=3000
```

## Dockerfile Template

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY package.json ./
COPY packages/*/package.json ./
RUN corepack enable && pnpm install
COPY . .
RUN pnpm -r exec tsc --outDir dist

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
CMD ["node", "dist/packages/backend/src/index.js"]
```
