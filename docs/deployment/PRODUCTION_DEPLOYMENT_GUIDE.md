# Production Deployment Guide - ITDO ERP v2 Authentication System

## Overview
This guide covers the deployment of the ITDO ERP v2 authentication system to production environment.

## Prerequisites

### 1. Infrastructure Requirements
- **Server**: Ubuntu 22.04 LTS or later
- **CPU**: Minimum 4 cores, recommended 8 cores
- **RAM**: Minimum 8GB, recommended 16GB
- **Storage**: 100GB SSD minimum
- **Network**: Static IP with HTTPS support

### 2. Software Requirements
- Python 3.13+
- PostgreSQL 15+
- Redis 7+
- Nginx (for reverse proxy)
- Podman or Docker
- uv (Python package manager)

### 3. External Services
- Keycloak instance for OAuth2/OIDC
- Google OAuth2 credentials for SSO
- SSL certificates (Let's Encrypt recommended)

## Pre-Deployment Checklist

- [ ] Production server provisioned
- [ ] Domain name configured
- [ ] SSL certificates obtained
- [ ] Database server ready
- [ ] Redis server ready
- [ ] Keycloak configured
- [ ] Google OAuth2 credentials ready
- [ ] Environment variables prepared
- [ ] Backup strategy defined

## Deployment Steps

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.13 python3.13-venv python3.13-dev \
    postgresql-client redis-tools nginx certbot python3-certbot-nginx \
    git curl build-essential

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### Step 2: Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash itdo-erp
sudo usermod -aG sudo itdo-erp

# Switch to application user
sudo su - itdo-erp

# Clone repository
git clone https://github.com/yourusername/ITDO_ERP2.git
cd ITDO_ERP2

# Checkout stable release
git checkout v2.0.0  # or appropriate tag
```

### Step 3: Environment Configuration

Create production environment file:

```bash
# Create .env.production
cat > backend/.env.production << 'EOF'
# Database
DATABASE_URL=postgresql://itdo_erp:SECURE_PASSWORD@localhost:5432/itdo_erp_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=SECURE_REDIS_PASSWORD

# Security
SECRET_KEY=GENERATE_SECURE_SECRET_KEY_HERE
JWT_SECRET_KEY=GENERATE_SECURE_JWT_SECRET_HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/v1/auth/google/callback

# Keycloak
KEYCLOAK_SERVER_URL=https://keycloak.your-domain.com
KEYCLOAK_REALM=itdo-erp
KEYCLOAK_CLIENT_ID=itdo-erp-backend
KEYCLOAK_CLIENT_SECRET=your-keycloak-secret

# CORS
CORS_ORIGINS=["https://your-domain.com", "https://app.your-domain.com"]

# Application
APP_NAME="ITDO ERP v2"
APP_VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Session
SESSION_TIMEOUT_MINUTES=480  # 8 hours default
SESSION_IDLE_TIMEOUT_MINUTES=30
SESSION_REMEMBER_ME_DAYS=30

# MFA
MFA_ISSUER_NAME="ITDO ERP"
MFA_ENFORCE_FOR_ADMIN=true
MFA_ENFORCE_FOR_EXTERNAL=true

# Email (for password reset)
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@your-domain.com
SMTP_FROM_NAME="ITDO ERP System"
EOF

# Set proper permissions
chmod 600 backend/.env.production
```

### Step 4: Database Setup

```bash
# Create production database
sudo -u postgres psql << EOF
CREATE USER itdo_erp WITH PASSWORD 'SECURE_PASSWORD';
CREATE DATABASE itdo_erp_prod OWNER itdo_erp;
GRANT ALL PRIVILEGES ON DATABASE itdo_erp_prod TO itdo_erp;
EOF

# Run migrations
cd backend
uv run alembic upgrade head
```

### Step 5: Application Installation

```bash
# Install dependencies
cd /home/itdo-erp/ITDO_ERP2/backend
uv sync --frozen

# Build frontend
cd ../frontend
npm ci --production
npm run build

# Create necessary directories
mkdir -p /home/itdo-erp/logs
mkdir -p /home/itdo-erp/uploads
```

### Step 6: Systemd Service Configuration

Create systemd service for the backend:

```bash
sudo tee /etc/systemd/system/itdo-erp-backend.service << 'EOF'
[Unit]
Description=ITDO ERP Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=itdo-erp
Group=itdo-erp
WorkingDirectory=/home/itdo-erp/ITDO_ERP2/backend
Environment="PATH=/home/itdo-erp/.local/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/itdo-erp/ITDO_ERP2/backend/.env.production
ExecStart=/home/itdo-erp/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable itdo-erp-backend
sudo systemctl start itdo-erp-backend
```

### Step 7: Nginx Configuration

Configure Nginx as reverse proxy:

```bash
sudo tee /etc/nginx/sites-available/itdo-erp << 'EOF'
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    # Frontend
    location / {
        root /home/itdo-erp/ITDO_ERP2/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/itdo-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: SSL Certificate Setup

```bash
# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Step 9: Security Hardening

```bash
# Configure firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable

# Set up fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure application security headers
# Add to Nginx configuration:
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
```

### Step 10: Monitoring Setup

```bash
# Install monitoring tools
sudo apt install prometheus-node-exporter

# Configure application metrics endpoint
# Add to backend configuration

# Set up log rotation
sudo tee /etc/logrotate.d/itdo-erp << 'EOF'
/home/itdo-erp/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 itdo-erp itdo-erp
    sharedscripts
    postrotate
        systemctl reload itdo-erp-backend
    endscript
}
EOF
```

## Post-Deployment Tasks

### 1. Verify Deployment

```bash
# Check service status
sudo systemctl status itdo-erp-backend

# Check application health
curl https://your-domain.com/api/v1/health

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "testpass"}'
```

### 2. Create Initial Admin User

```bash
cd /home/itdo-erp/ITDO_ERP2/backend
uv run python scripts/create_admin.py \
  --email admin@your-domain.com \
  --password SECURE_ADMIN_PASSWORD \
  --name "System Administrator"
```

### 3. Configure Backup

```bash
# Database backup script
sudo tee /home/itdo-erp/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/itdo-erp/backups"
DB_NAME="itdo_erp_prod"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -U itdo_erp -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /home/itdo-erp/backup-db.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/itdo-erp/backup-db.sh") | crontab -
```

### 4. Performance Tuning

```bash
# PostgreSQL tuning
sudo -u postgres psql << EOF
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET min_wal_size = '2GB';
ALTER SYSTEM SET max_wal_size = '8GB';
EOF

sudo systemctl restart postgresql
```

## Troubleshooting

### Common Issues

1. **Service fails to start**
   ```bash
   # Check logs
   sudo journalctl -u itdo-erp-backend -f
   
   # Check permissions
   ls -la /home/itdo-erp/ITDO_ERP2/backend/.env.production
   ```

2. **Database connection errors**
   ```bash
   # Test connection
   psql -h localhost -U itdo_erp -d itdo_erp_prod
   
   # Check PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

3. **Authentication failures**
   ```bash
   # Check JWT secret
   grep JWT_SECRET /home/itdo-erp/ITDO_ERP2/backend/.env.production
   
   # Verify Google OAuth settings
   curl https://your-domain.com/api/v1/auth/google/login
   ```

## Rollback Procedure

If deployment fails:

```bash
# Stop services
sudo systemctl stop itdo-erp-backend

# Restore database from backup
gunzip < /home/itdo-erp/backups/db_backup_TIMESTAMP.sql.gz | psql -U itdo_erp -d itdo_erp_prod

# Checkout previous version
cd /home/itdo-erp/ITDO_ERP2
git checkout previous-version-tag

# Restart services
sudo systemctl start itdo-erp-backend
```

## Security Checklist

- [ ] All default passwords changed
- [ ] Firewall configured and enabled
- [ ] SSL certificates installed and auto-renewal configured
- [ ] Database access restricted to localhost
- [ ] Redis password set
- [ ] Application logs not exposing sensitive data
- [ ] Regular backups configured
- [ ] Monitoring and alerting set up
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured

## Support

For issues or questions:
- Check application logs: `/home/itdo-erp/logs/`
- System logs: `sudo journalctl -u itdo-erp-backend`
- Database logs: `/var/log/postgresql/`