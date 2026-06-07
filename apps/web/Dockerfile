# Built from the repo root so the npm workspace shares the single root lockfile.
#   docker build -f apps/web/Dockerfile .
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_BACKEND_URL="http://localhost:8080"
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}
ARG NEXT_PUBLIC_FIREBASE_API_KEY=""
ENV NEXT_PUBLIC_FIREBASE_API_KEY=${NEXT_PUBLIC_FIREBASE_API_KEY}
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=""
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN}
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID=""
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=${NEXT_PUBLIC_FIREBASE_PROJECT_ID}
ARG NEXT_PUBLIC_FIREBASE_APP_ID=""
ENV NEXT_PUBLIC_FIREBASE_APP_ID=${NEXT_PUBLIC_FIREBASE_APP_ID}
RUN npm run build --workspace @mathquest/web

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Standalone output (monorepo layout): server + traced node_modules at the root,
# the app itself under apps/web/.
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "apps/web/server.js"]
