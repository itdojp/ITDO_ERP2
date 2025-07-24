#!/bin/bash
# ITDO ERP v2 - Production Deployment Script
# CC03 v51.0 Production Docker Compose Deployment

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="compose-prod.yaml"
ENV_FILE=".env.prod"
ENV_EXAMPLE=".env.prod.example"
BACKUP_DIR="backups"
LOG_DIR="logs"

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

success() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Print header
print_header() {
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "🚀 ITDO ERP v2 Production Deployment"
    echo "   CC03 v51.0 Docker Compose Implementation"
    echo "=================================================="
    echo -e "${NC}"
    echo "📊 Production Services:"
    echo "  • NGINX Reverse Proxy & Load Balancer"
    echo "  • Backend API (FastAPI + Python)"
    echo "  • Frontend App (React + TypeScript)"
    echo "  • PostgreSQL Database (High Performance)"
    echo "  • Redis Cache & Session Store"
    echo "  • Keycloak Authentication Server"
    echo "  • Automated Database Backup"
    echo "  • Centralized Logging (Fluentd)"
    echo "  • Health Monitoring & Alerting"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check if running from correct directory
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Must run from infra/ directory. $COMPOSE_FILE not found."
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
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        warn "Production environment file $ENV_FILE not found!"
        if [[ -f "$ENV_EXAMPLE" ]]; then
            info "Creating $ENV_FILE from template..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            echo -e "${YELLOW}"
            echo "⚠️  IMPORTANT: Configure $ENV_FILE with production values before deployment!"
            echo "   Update all CHANGE_ME values with secure production credentials."
            echo -e "${NC}"
            read -p "Press Enter after configuring environment file, or Ctrl+C to abort..."
        else
            error "No environment template found. Cannot proceed."
        fi
    fi
    
    # Validate environment file
    source "$ENV_FILE"
    if [[ "${POSTGRES_PASSWORD:-}" == *"CHANGE_ME"* ]] || [[ "${SECRET_KEY:-}" == *"CHANGE_ME"* ]]; then
        error "Environment file contains template values. Update $ENV_FILE with production credentials."
    fi
    
    # Check container images
    info "Verifying container image availability..."
    if ! $CONTAINER_ENGINE image inspect ghcr.io/itdojp/itdo_erp2-backend:latest &>/dev/null; then
        warn "Backend image not found locally. Will pull during deployment."
    fi
    if ! $CONTAINER_ENGINE image inspect ghcr.io/itdojp/itdo_erp2-frontend:latest &>/dev/null; then
        warn "Frontend image not found locally. Will pull during deployment."
    fi
    
    success "Prerequisites check completed"
}

# Create required directories
create_directories() {
    log "Creating required directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "nginx/logs"
    mkdir -p "nginx/ssl"
    mkdir -p "postgres"
    mkdir -p "fluentd"
    
    # Set proper permissions
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "nginx/logs"
    
    success "Directory structure created"
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certs() {
    log "Checking SSL certificates..."
    
    SSL_DIR="nginx/ssl"
    CERT_FILE="$SSL_DIR/itdo-erp.com.crt"
    KEY_FILE="$SSL_DIR/itdo-erp.com.key"
    DHPARAM_FILE="$SSL_DIR/dhparam.pem"
    
    if [[ ! -f "$CERT_FILE" ]] || [[ ! -f "$KEY_FILE" ]]; then
        warn "SSL certificates not found. Generating self-signed certificates..."
        warn "For production, replace with proper SSL certificates from a CA."
        
        # Generate private key
        openssl genrsa -out "$KEY_FILE" 2048
        
        # Generate certificate
        openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 \
            -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO/OU=ERP/CN=itdo-erp.com/emailAddress=admin@itdo-erp.com"
        
        # Generate DH parameters (in background for speed)
        if [[ ! -f "$DHPARAM_FILE" ]]; then
            info "Generating DH parameters (this may take a few minutes)..."
            openssl dhparam -out "$DHPARAM_FILE" 2048 &
        fi
        
        success "Self-signed SSL certificates generated"
        warn "Replace with proper certificates for production use!"
    else
        info "SSL certificates found"
    fi
}

# Validate configuration
validate_config() {
    log "Validating Docker Compose configuration..."
    
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config > /dev/null; then
        error "Docker Compose configuration validation failed"
    fi
    
    success "Configuration validation passed"
}

# Pull container images
pull_images() {
    log "Pulling latest container images..."
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    success "Container images updated"
}

# Deploy services
deploy_services() {
    log "Deploying production services..."
    
    # Stop existing services
    info "Stopping existing services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans || true
    
    # Start services in dependency order
    info "Starting database services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    sleep 30
    
    # Start authentication service
    info "Starting authentication service..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d keycloak
    
    # Wait for Keycloak to initialize
    info "Waiting for Keycloak to initialize..."
    sleep 60
    
    # Start application services
    info "Starting application services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend frontend
    
    # Wait for applications to be ready
    info "Waiting for applications to start..."
    sleep 30
    
    # Start reverse proxy
    info "Starting reverse proxy..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d nginx
    
    # Start supporting services
    info "Starting backup and logging services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d db-backup fluentd
    
    success "All services deployed successfully"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment health..."
    
    # Check service status
    info "Checking service status..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    # Health check endpoints
    info "Performing health checks..."
    
    # Wait a bit for services to fully start
    sleep 10
    
    # Check PostgreSQL
    if $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U itdo_user -d itdo_erp; then
        success "PostgreSQL health check passed"
    else
        warn "PostgreSQL health check failed"
    fi
    
    # Check Redis
    if $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q PONG; then
        success "Redis health check passed"
    else
        warn "Redis health check failed"
    fi
    
    # Check backend API
    if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
        success "Backend API health check passed"
    else
        warn "Backend API health check failed - service may still be starting"
    fi
    
    # Check frontend
    if curl -f -s http://localhost:3000/health > /dev/null; then
        success "Frontend health check passed"
    else
        warn "Frontend health check failed - service may still be starting"
    fi
    
    # Check NGINX
    if curl -f -s http://localhost/health > /dev/null; then
        success "NGINX health check passed"
    else
        warn "NGINX health check failed"
    fi
    
    success "Deployment verification completed"
}

# Show deployment summary
show_summary() {
    echo -e "${PURPLE}"
    echo "🎉 ITDO ERP v2 Production Deployment Complete!"
    echo "=============================================="
    echo -e "${NC}"
    
    echo -e "${BLUE}=== Service URLs ===${NC}"
    echo "🌐 Main Application: http://localhost (HTTPS: https://localhost)"
    echo "🔐 Authentication: http://localhost:8080 (Keycloak)"
    echo "📊 API Endpoint: http://localhost:8000/api/v1"
    echo "🎨 Frontend: http://localhost:3000"
    echo "🗄️ Database: localhost:5432"
    echo "💾 Cache: localhost:6379"
    echo ""
    
    echo -e "${BLUE}=== Production Features ===${NC}"
    echo "✅ NGINX Reverse Proxy with SSL/TLS"
    echo "✅ Health Monitoring & Auto-restart"
    echo "✅ Automated Database Backups"
    echo "✅ Centralized Logging"
    echo "✅ Resource Limits & Performance Tuning"
    echo "✅ Security Headers & Rate Limiting"
    echo "✅ Container Image Registry Integration"
    echo ""
    
    echo -e "${BLUE}=== Management Commands ===${NC}"
    echo "📊 View status: $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE ps"
    echo "📋 View logs: $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE logs -f [service]"
    echo "🔄 Restart service: $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE restart [service]"
    echo "🛑 Stop all: $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE down"
    echo "🔧 Update images: $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE pull && $COMPOSE_CMD -f $COMPOSE_FILE --env-file $ENV_FILE up -d"
    echo ""
    
    echo -e "${YELLOW}=== Important Security Notes ===${NC}"
    echo "⚠️  Update SSL certificates with proper CA-signed certificates"
    echo "⚠️  Review and secure all environment variables in $ENV_FILE"
    echo "⚠️  Configure firewall rules for production deployment"
    echo "⚠️  Set up regular backup verification and restore testing"
    echo "⚠️  Monitor resource usage and adjust limits as needed"
    echo "⚠️  Enable log aggregation and monitoring in production"
    echo ""
    
    success "Production deployment ready for use!"
}

# Cleanup function
cleanup() {
    if [[ ${1:-} == "all" ]]; then
        warn "Performing complete infrastructure cleanup..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --volumes --remove-orphans
        success "Complete cleanup completed"
    else
        info "Use '$0 cleanup all' to perform complete cleanup (including volumes)"
        info "⚠️  This will destroy all data and cannot be undone!"
    fi
}

# Backup function
backup() {
    log "Creating production backup..."
    
    BACKUP_NAME="itdo-erp-backup-$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup database
    info "Backing up PostgreSQL database..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U itdo_user -d itdo_erp > "$BACKUP_PATH/postgres-dump.sql"
    
    # Backup Redis data
    info "Backing up Redis data..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
        redis-cli --rdb - > "$BACKUP_PATH/redis-dump.rdb"
    
    # Backup volumes
    info "Backing up application data..."
    cp -r nginx/logs "$BACKUP_PATH/" 2>/dev/null || true
    
    # Create archive
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
    rm -rf "$BACKUP_PATH"
    
    success "Backup created: $BACKUP_PATH.tar.gz"
}

# Main deployment function
main() {
    case ${1:-deploy} in
        "deploy")
            print_header
            check_prerequisites
            create_directories
            generate_ssl_certs
            validate_config
            pull_images
            deploy_services
            verify_deployment
            show_summary
            ;;
        "cleanup")
            cleanup ${2:-}
            ;;
        "backup")
            backup
            ;;
        "status")
            info "Checking deployment status..."
            if [[ -f "$COMPOSE_FILE" ]] && [[ -f "$ENV_FILE" ]]; then
                $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
            else
                error "Configuration files not found"
            fi
            ;;
        "logs")
            if [[ -n ${2:-} ]]; then
                $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$2"
            else
                $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
            fi
            ;;
        "restart")
            if [[ -n ${2:-} ]]; then
                $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart "$2"
            else
                $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
            fi
            ;;
        "update")
            log "Updating production deployment..."
            pull_images
            $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
            verify_deployment
            ;;
        "help")
            echo "Usage: $0 [deploy|cleanup|backup|status|logs|restart|update|help]"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy the complete production infrastructure"
            echo "  cleanup - Remove deployed resources (use 'cleanup all' for volumes)"
            echo "  backup  - Create backup of database and application data"
            echo "  status  - Show current deployment status"
            echo "  logs    - Show logs (use 'logs [service]' for specific service)"
            echo "  restart - Restart services (use 'restart [service]' for specific service)"
            echo "  update  - Update images and restart services"
            echo "  help    - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy           # Full production deployment"
            echo "  $0 status           # Check service status"
            echo "  $0 logs backend     # View backend logs"
            echo "  $0 backup           # Create backup"
            echo "  $0 cleanup all      # Complete cleanup (DESTRUCTIVE)"
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Script execution
main "$@"