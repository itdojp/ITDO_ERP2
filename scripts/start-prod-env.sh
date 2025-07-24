#!/bin/bash
# ITDO ERP v2 - Production Environment Startup Script
# CC03 v54.0 - Docker Compose Integration

set -euo pipefail

# Configuration
PROJECT_ROOT="/home/work/ITDO_ERP2"
INFRA_DIR="$PROJECT_ROOT/infra"
COMPOSE_FILE="$INFRA_DIR/compose-prod.yaml"
ENV_FILE="$INFRA_DIR/.env.prod"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Print header
echo -e "${BLUE}"
echo "==============================================="
echo "🚀 ITDO ERP v2 Production Environment Startup"
echo "   CC03 v54.0 Docker Compose Integration"
echo "==============================================="
echo -e "${NC}"

# Change to infra directory
log "Changing to infra directory..."
cd "$INFRA_DIR" || error "Cannot change to infra directory: $INFRA_DIR"

# Check prerequisites
log "Checking prerequisites..."

# Check compose file
if [[ ! -f "$COMPOSE_FILE" ]]; then
    error "Docker Compose file not found: $COMPOSE_FILE"
fi

# Check environment file
if [[ ! -f "$ENV_FILE" ]]; then
    warn "Production environment file not found: $ENV_FILE"
    if [[ -f ".env.prod.example" ]]; then
        info "Creating production environment from template..."
        cp ".env.prod.example" "$ENV_FILE"
        warn "Please configure $ENV_FILE with production values!"
    else
        error "No environment template found. Cannot proceed."
    fi
fi

# Check Docker/Podman
if command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
    CONTAINER_ENGINE="podman"
    info "Using Podman with podman-compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    CONTAINER_ENGINE="docker"
    info "Using Docker with docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    CONTAINER_ENGINE="docker"
    info "Using Docker with compose plugin"
else
    error "Neither docker-compose nor podman-compose is available"
fi

# Create required directories
log "Creating required directories..."
mkdir -p /opt/itdo-erp/{data,logs,cache,backups}/{postgres,redis,backend,frontend,keycloak,nginx}
mkdir -p /opt/itdo-erp/data/postgres-wal

# Validate configuration
log "Validating Docker Compose configuration..."
if ! $COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod config > /dev/null; then
    error "Docker Compose configuration validation failed"
fi

# Stop any existing containers
log "Stopping any existing production containers..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod down --remove-orphans || true

# Start production environment
log "Starting ITDO ERP v2 production environment..."

info "Starting database services..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod up -d postgres redis

# Wait for database to be ready
info "Waiting for database to be ready..."
sleep 30

info "Starting authentication service..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod up -d keycloak

# Wait for Keycloak to initialize
info "Waiting for Keycloak to initialize..."
sleep 60

info "Starting application services..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod up -d backend frontend

# Wait for applications to start
info "Waiting for applications to start..."
sleep 30

info "Starting reverse proxy..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod up -d nginx

# Final startup wait
sleep 15

# Verify services
log "Verifying service status..."
$COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod ps

# Success message
echo -e "${GREEN}"
echo "🎉 ITDO ERP v2 Production Environment Started Successfully!"
echo "=========================================================="
echo -e "${NC}"

echo -e "${BLUE}=== Service URLs ===${NC}"
echo "🌐 Main Application: https://itdo-erp.com (or http://localhost)"
echo "🔐 Authentication: http://localhost:8080 (Keycloak)"
echo "📊 API Endpoint: http://localhost:8000/api/v1"
echo "🎨 Frontend: http://localhost:3000"
echo "🗄️ PostgreSQL: localhost:5432"
echo "💾 Redis: localhost:6379"
echo ""

echo -e "${BLUE}=== Management Commands ===${NC}"
echo "📊 View status: $COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod ps"
echo "📋 View logs: $COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod logs -f [service]"
echo "🛑 Stop all: $COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod down"
echo "🔧 Restart: $COMPOSE_CMD -f compose-prod.yaml --env-file .env.prod restart [service]"
echo ""

log "Production environment startup completed!"