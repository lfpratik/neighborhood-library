# ------------------------
# Base image
# ------------------------
FROM node:20-alpine AS base

# ------------------------
# Dependencies
# ------------------------
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ------------------------
# Build
# ------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ------------------------
# Production runner
# ------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# ✅ Install curl for healthcheck
RUN apk add --no-cache curl

# ✅ Non-root user (security best practice)
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy required files only
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set permissions
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 3000

CMD ["node", "server.js"]
