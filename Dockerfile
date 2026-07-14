FROM node:20-alpine AS builder
WORKDIR /app

# pnpm setup
RUN corepack enable && corepack prepare pnpm@9 --activate

COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY package.json tsconfig.base.json turbo.json ./
COPY packages/*/package.json ./packages/
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm -r exec tsc --noEmit
RUN pnpm -r exec tsc --outDir dist

FROM node:20-alpine AS runner
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate
COPY --from=builder /app/pnpm-lock.yaml /app/pnpm-workspace.yaml ./
COPY --from=builder /app/package.json ./
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "packages/backend/dist/server.js"]
