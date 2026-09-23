# syntax=docker/dockerfile:1

# Build

FROM node:24-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci \
    --no-audit \
    --no-fund

COPY . .

ARG VITE_N8N_CHAT_WEBHOOK_URL
ARG VITE_API_BASE_URL

ENV VITE_N8N_CHAT_WEBHOOK_URL=${VITE_N8N_CHAT_WEBHOOK_URL} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# Runtime

FROM nginx:stable-alpine3.24 AS runtime

RUN rm -f /etc/nginx/conf.d/default.conf \
    && cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    listen [::]:80;

    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    server_tokens off;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "microphone=(self)" always;

    location = /health {
        access_log off;
        default_type text/plain;
        return 200 "ok";
    }

    location /assets/ {
        try_files $uri =404;

        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        add_header Cache-Control "no-cache" always;
        try_files $uri $uri/ /index.html;
    }
}
EOF

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK \
    --interval=10s \
    --timeout=5s \
    --start-period=5s \
    --retries=3 \
    CMD wget -q -O - http://127.0.0.1/health | grep -q '^ok$' || exit 1

CMD ["nginx", "-g", "daemon off;"]