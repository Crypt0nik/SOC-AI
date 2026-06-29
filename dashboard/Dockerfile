# Multi-stage build: Node for Vite build → nginx for production serving
ARG VITE_API_URL=http://localhost:8000

# ── Stage 1: build ────────────────────────────────────────────
FROM node:20 AS builder

WORKDIR /app

COPY dashboard/package*.json ./
RUN npm install

COPY dashboard/ .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Stage 2: serve with nginx ─────────────────────────────────
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
