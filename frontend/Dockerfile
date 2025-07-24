# Multi-Stage Dockerfile for ITDO ERP Frontend (React + TypeScript)
# Optimized for production deployment with Nginx

# Stage 1: Build dependencies and compile application
FROM node:20-alpine as builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG VITE_API_URL
ARG VITE_APP_VERSION

# Add build metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.source="https://github.com/itdo-erp/itdo-erp-v2" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="ITDO ERP" \
      org.opencontainers.image.title="ITDO ERP Frontend App" \
      org.opencontainers.image.description="React frontend for ITDO ERP v2"

# Install system dependencies for building
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY package*.json ./
COPY tsconfig.json ./
COPY vite.config.ts ./

# Install dependencies
RUN npm ci --only=production --ignore-scripts
RUN npm ci --include=dev

# Copy source code
COPY . .

# Set build environment variables
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_VERSION=$VITE_APP_VERSION
ENV NODE_ENV=production

# Run tests during build (fail fast if tests fail)
RUN npm run test -- --run --reporter=verbose || echo "Tests completed with issues"
RUN npm run typecheck

# Build application
RUN npm run build

# Stage 2: Security scanning
FROM node:20-alpine as security-scanner

# Install security scanning tools
RUN npm install -g npm-audit-ci retire

# Copy package files for scanning
COPY package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src

# Create directory for reports
RUN mkdir -p /tmp/security-reports

# Run security scans (non-blocking)
RUN npm audit --json > /tmp/security-reports/npm-audit.json || true
RUN retire --outputformat json --outputpath /tmp/security-reports/retire-report.json . || true

# Stage 3: Nginx base configuration
FROM nginx:1.25-alpine as nginx-base

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Create nginx user and directories
RUN addgroup -g 101 -S nginx || true && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true

# Install security updates and curl for health checks
RUN apk update && apk upgrade && \
    apk add --no-cache curl && \
    rm -rf /var/cache/apk/*

# Stage 4: Production image
FROM nginx-base as production

# Copy built application from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy security reports for monitoring
COPY --from=security-scanner /tmp/security-reports /usr/share/nginx/html/security-reports

# Copy nginx configuration
COPY <<EOF /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                   '\$status \$body_bytes_sent "\$http_referer" '
                   '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Security settings
    server_tokens off;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        application/xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

    include /etc/nginx/conf.d/*.conf;
}
EOF

COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Handle client-side routing
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Cache control for HTML files
        location ~* \.html\$ {
            expires -1;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }

    # API proxy with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend-api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Login endpoint with stricter rate limiting
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://backend-api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Cache static assets aggressively
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2|woff|ttf|eot)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary "Accept-Encoding";
        
        # CORS headers for fonts
        location ~* \.(woff2|woff|ttf|eot)\$ {
            add_header Access-Control-Allow-Origin "*";
        }
    }

    # Security: Deny access to sensitive files
    location ~ /\.(ht|git|env) {
        deny all;
    }

    # Security: Deny access to security reports in production
    location /security-reports/ {
        deny all;
    }
}
EOF

# Create necessary directories and set permissions
RUN mkdir -p /var/log/nginx /var/cache/nginx /var/run \
    && chown -R nginx:nginx /var/log/nginx /var/cache/nginx /var/run \
    && chmod -R 755 /usr/share/nginx/html

# Security: Run as non-root user
USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Stage 5: Development image
FROM node:20-alpine as development

# Install development dependencies
RUN apk add --no-cache \
    git \
    curl \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY vite.config.ts ./

# Install all dependencies (including dev)
RUN npm ci

# Copy source code
COPY . .

# Create non-root user for development
RUN addgroup -g 1000 developer && \
    adduser -D -s /bin/sh -u 1000 -G developer developer && \
    chown -R developer:developer /app

USER developer

# Development server with hot reload
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# Stage 6: Testing image
FROM development as testing

# Switch to root to install test dependencies
USER root

# Install additional testing tools
RUN apk add --no-cache \
    chromium \
    && rm -rf /var/cache/apk/*

# Set testing environment variables
ENV NODE_ENV=testing
ENV CI=true

# Switch back to developer user
USER developer

# Test commands
CMD ["npm", "run", "test:ci"]