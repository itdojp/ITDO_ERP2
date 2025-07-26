# ITDO ERP System v2 - Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the ITDO ERP System v2 in various environments, from local development to production. The system follows a hybrid architecture with containerized data services and local development runtime.

## 🏗️ Architecture Overview

### Deployment Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Environment                     │
├─────────────────────────────────────────────────────────────────┤
│  Load Balancer → Application Servers → Database Cluster        │
│  (Nginx/HAProxy)   (Multiple FastAPI)    (PostgreSQL + Redis)  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Development Environment                      │
├─────────────────────────────────────────────────────────────────┤
│  Local Development → Containerized Data Services               │
│  (FastAPI + React)    (PostgreSQL + Redis + Keycloak)         │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB available space
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+

#### Recommended Production Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB+ SSD
- **OS**: Ubuntu 22.04 LTS

### Required Software

#### Development Environment
- **Python**: 3.13+
- **Node.js**: 18+
- **Podman**: Latest stable version
- **Git**: 2.30+
- **uv**: Latest version

#### Production Environment
- **Python**: 3.13+
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Nginx**: 1.20+
- **Systemd**: For service management

### Installation Commands

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3.13-dev -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Podman
sudo apt install podman -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python@3.13 node@18 podman git
brew install uv
```

## 🚀 Development Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/itdojp/ITDO_ERP2.git
cd ITDO_ERP2
```

### 2. Setup Development Environment
```bash
# Initialize development environment
make setup-dev

# This command will:
# - Create Python virtual environment with uv
# - Install backend dependencies
# - Install frontend dependencies
# - Set up pre-commit hooks
# - Create necessary directories
```

### 3. Configure Environment Variables
```bash
# Copy environment template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files
nano backend/.env
nano frontend/.env
```

#### Backend Environment Variables (.env)
```env
# Database Configuration
DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp_db
DATABASE_TEST_URL=sqlite:///./test.db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=itdo-erp
KEYCLOAK_CLIENT_ID=itdo-erp-backend
KEYCLOAK_CLIENT_SECRET=your-client-secret

# Application Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

#### Frontend Environment Variables (.env)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Authentication Configuration
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=itdo-erp
VITE_KEYCLOAK_CLIENT_ID=itdo-erp-frontend

# Development Settings
VITE_DEBUG=true
VITE_LOG_LEVEL=info
```

### 4. Start Data Services
```bash
# Start containerized data services
make start-data

# This will start:
# - PostgreSQL database (port 5432)
# - Redis cache (port 6379)
# - Keycloak authentication (port 8080)
# - pgAdmin database admin (port 8081)
```

### 5. Initialize Database
```bash
# Run database migrations
cd backend
uv run alembic upgrade head

# Seed initial data (optional)
uv run python scripts/seed_data.py
```

### 6. Start Development Servers
```bash
# Terminal 1: Start backend server
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend server
cd frontend
npm run dev
```

### 7. Verify Installation
- **Backend API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Database Admin**: http://localhost:8081
- **Keycloak Admin**: http://localhost:8080/admin

## 🏭 Production Deployment

### Option 1: Traditional Server Deployment

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3.13 python3.13-venv nginx postgresql redis-server supervisor -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Database Setup
```bash
# Configure PostgreSQL
sudo -u postgres psql
```
```sql
-- Create database and user
CREATE DATABASE itdo_erp_db;
CREATE USER itdo_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE itdo_erp_db TO itdo_user;
\q
```

#### 3. Application Deployment
```bash
# Create application user
sudo useradd -m -s /bin/bash itdo

# Create application directory
sudo mkdir -p /opt/itdo-erp
sudo chown itdo:itdo /opt/itdo-erp

# Switch to application user
sudo -u itdo -i

# Clone repository
cd /opt/itdo-erp
git clone https://github.com/itdojp/ITDO_ERP2.git .

# Setup Python environment
cd backend
uv sync --frozen

# Build frontend
cd ../frontend
npm ci --production
npm run build
```

#### 4. Configuration Files

##### Systemd Service (/etc/systemd/system/itdo-erp.service)
```ini
[Unit]
Description=ITDO ERP System v2
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=itdo
Group=itdo
WorkingDirectory=/opt/itdo-erp/backend
Environment=PATH=/opt/itdo-erp/backend/.venv/bin
ExecStart=/opt/itdo-erp/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

##### Nginx Configuration (/etc/nginx/sites-available/itdo-erp)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;

    # Frontend static files
    location / {
        root /opt/itdo-erp/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
}
```

#### 5. Start Services
```bash
# Enable and start services
sudo systemctl enable postgresql redis nginx itdo-erp
sudo systemctl start postgresql redis nginx itdo-erp

# Check service status
sudo systemctl status itdo-erp
```

### Option 2: Docker Deployment

#### 1. Create Dockerfiles

##### Backend Dockerfile
```dockerfile
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Run migrations and start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

##### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 2. Docker Compose Configuration

##### docker-compose.prod.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: itdo_erp_db
      POSTGRES_USER: itdo_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - itdo-network

  redis:
    image: redis:7-alpine
    networks:
      - itdo-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://itdo_user:${DB_PASSWORD}@db:5432/itdo_erp_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - itdo-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - itdo-network

volumes:
  postgres_data:

networks:
  itdo-network:
    driver: bridge
```

#### 3. Deploy with Docker Compose
```bash
# Set environment variables
export DB_PASSWORD=your_secure_password

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head
```

### Option 3: Cloud Deployment (AWS)

#### 1. Infrastructure as Code (Terraform)

##### main.tf
```hcl
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "itdo_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "itdo-erp-vpc"
  }
}

# Application Load Balancer
resource "aws_lb" "itdo_alb" {
  name               = "itdo-erp-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = false
}

# ECS Cluster
resource "aws_ecs_cluster" "itdo_cluster" {
  name = "itdo-erp-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "itdo_db" {
  identifier             = "itdo-erp-db"
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_encrypted      = true

  db_name  = "itdo_erp_db"
  username = "itdo_user"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.itdo_db_subnet_group.name

  backup_retention_period = 7
  backup_window          = "07:00-09:00"
  maintenance_window     = "sun:09:00-sun:11:00"

  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "itdo_cache_subnet" {
  name       = "itdo-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "itdo_redis" {
  cluster_id           = "itdo-erp-redis"
  engine               = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.itdo_cache_subnet.name
  security_group_ids  = [aws_security_group.redis_sg.id]
}
```

#### 2. ECS Task Definitions

##### backend-task-definition.json
```json
{
  "family": "itdo-erp-backend",
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/itdo-erp-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://itdo_user:password@db-endpoint:5432/itdo_erp_db"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://redis-endpoint:6379/0"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/itdo-erp-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

#### .github/workflows/deploy.yml
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: |
          cd backend
          uv sync
      
      - name: Run tests
        run: |
          cd backend
          uv run pytest
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push backend image
        run: |
          cd backend
          docker build -t $ECR_REGISTRY/itdo-erp-backend:$GITHUB_SHA .
          docker push $ECR_REGISTRY/itdo-erp-backend:$GITHUB_SHA
      
      - name: Build and push frontend image
        run: |
          cd frontend
          docker build -t $ECR_REGISTRY/itdo-erp-frontend:$GITHUB_SHA .
          docker push $ECR_REGISTRY/itdo-erp-frontend:$GITHUB_SHA
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster itdo-erp-cluster \
            --service itdo-erp-backend \
            --force-new-deployment
```

## 📊 Monitoring & Logging

### Application Monitoring

#### 1. Health Checks
```bash
# Backend health check
curl http://localhost:8000/health

# Database connectivity check
curl http://localhost:8000/health/detailed
```

#### 2. Log Configuration

##### Python Logging (backend/app/core/config.py)
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

#### 3. System Monitoring

##### Prometheus Configuration (prometheus.yml)
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'itdo-erp-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Performance Monitoring

#### 1. Database Performance
```sql
-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Monitor database connections
SELECT * FROM pg_stat_activity;
```

#### 2. Application Performance
```python
# Add performance monitoring middleware
from time import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🔒 Security Considerations

### 1. Environment Security
```bash
# Set proper file permissions
chmod 600 backend/.env
chmod 600 frontend/.env

# Secure database files
sudo chmod 700 /var/lib/postgresql/15/main/
```

### 2. Network Security
```bash
# Configure firewall (UFW)
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8000/tcp  # Block direct backend access
```

### 3. SSL/TLS Configuration
```bash
# Install Let's Encrypt certificates
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🔧 Maintenance

### Regular Maintenance Tasks

#### 1. Database Maintenance
```bash
# Backup database
pg_dump -U itdo_user -h localhost itdo_erp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Vacuum and analyze
sudo -u postgres psql -d itdo_erp_db -c "VACUUM ANALYZE;"
```

#### 2. Log Rotation
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/itdo-erp << EOF
/opt/itdo-erp/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload itdo-erp
    endscript
}
EOF
```

#### 3. System Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
cd /opt/itdo-erp/backend
uv sync --upgrade

# Restart services
sudo systemctl restart itdo-erp
```

## 🆘 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
sudo -u postgres psql -c "SELECT version();"

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 2. Application Startup Issues
```bash
# Check application logs
sudo journalctl -u itdo-erp -f

# Check Python environment
cd /opt/itdo-erp/backend
uv run python -c "import app.main; print('OK')"
```

#### 3. Performance Issues
```bash
# Check system resources
htop
df -h
free -m

# Check database performance
sudo -u postgres psql -d itdo_erp_db -c "SELECT * FROM pg_stat_activity;"
```

## 📚 Additional Resources

### Documentation Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Nginx Documentation](https://nginx.org/en/docs/)

### Support Contacts
- **Technical Support**: tech-support@itdo.com
- **DevOps Team**: devops@itdo.com
- **Emergency Hotline**: +1-555-ITDO-911

---

## 📝 Document Information

- **Version**: 1.0
- **Last Updated**: 2025-01-26
- **Maintained By**: ITDO DevOps Team
- **Review Cycle**: Monthly

---

*This document is part of the ITDO ERP System v2 technical documentation suite.*