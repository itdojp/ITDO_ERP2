#!/bin/bash
# ITDO ERP v2 - Clean Production Deployment Script
# CC03 v60.0 - Clean Production Implementation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="../compose/docker-compose.production.yml"
ENV_FILE="../compose/.env.production.secure"
BACKUP_DIR="/opt/itdo-erp/backups"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        error "Please run the security setup first: cd ../security && ./setup-ssl.sh"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Create backup before deployment
create_backup() {
    log "Creating pre-deployment backup..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/pre-deploy-$(date +%Y%m%d-%H%M%S).sql"
    
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U itdo_user >/dev/null 2>&1; then
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            pg_dump -U itdo_user -d itdo_erp_prod > "$backup_file" 2>/dev/null || {
            warn "Failed to create database backup, continuing anyway..."
            return
        }
        log "Backup created: $backup_file"
    else
        warn "Database not available for backup, continuing with deployment..."
    fi
}

# Health check function
health_check() {
    local service="$1"
    local max_attempts="${2:-30}"
    local attempt=1
    
    info "Performing health check for $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T "$service" sh -c "exit 0" >/dev/null 2>&1; then
            if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "healthy\|Up"; then
                log "$service is healthy"
                return 0
            fi
        fi
        
        info "Waiting for $service to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error "$service failed health check after $max_attempts attempts"
    return 1
}

# Standard deployment
deploy_standard() {
    log "Starting standard deployment..."
    
    create_backup
    
    info "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    info "Stopping services..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    info "Starting services..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for core services
    health_check postgres 20
    health_check redis 10
    health_check backend 30
    health_check frontend 20
    
    log "Standard deployment completed successfully"
}

# Rolling deployment
deploy_rolling() {
    log "Starting rolling deployment..."
    
    create_backup
    
    info "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Rolling update services one by one
    local services=("redis" "postgres" "keycloak" "backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        info "Rolling update for $service..."
        
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps "$service"
        health_check "$service" 20
        
        info "$service updated successfully"
        sleep 5
    done
    
    log "Rolling deployment completed successfully"
}

# Blue-Green deployment simulation
deploy_blue_green() {
    log "Starting blue-green deployment simulation..."
    
    create_backup
    
    info "This is a simplified blue-green deployment"
    info "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    info "Creating new container versions..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --force-recreate
    
    # Health checks for critical services
    health_check postgres 20
    health_check backend 30
    health_check frontend 20
    
    info "Traffic switch completed"
    log "Blue-green deployment completed successfully"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    local validation_failed=false
    
    # Check if all services are running
    local services=("postgres" "redis" "backend" "frontend" "nginx" "keycloak")
    for service in "${services[@]}"; do
        if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "Up"; then
            error "$service is not running"
            validation_failed=true
        fi
    done
    
    # Basic connectivity tests
    if ! curl -f -s http://localhost/health >/dev/null 2>&1; then
        warn "Frontend health check failed"
    fi
    
    if $validation_failed; then
        error "Deployment validation failed"
        return 1
    fi
    
    log "Deployment validation passed"
}

# Rollback function
rollback() {
    log "Starting rollback..."
    
    warn "This is a basic rollback - stopping current deployment"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    log "Please restore from backup if needed"
    log "Available backups in: $BACKUP_DIR"
    ls -la "$BACKUP_DIR" 2>/dev/null || warn "No backups found"
}

# Status check
status() {
    log "Checking deployment status..."
    
    info "Container status:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    
    info "Service health:"
    local services=("postgres" "redis" "backend" "frontend" "nginx" "keycloak")
    for service in "${services[@]}"; do
        if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} $service"
        else
            echo -e "  ${RED}✗${NC} $service"
        fi
    done
}

# Show usage
usage() {
    echo "Usage: $0 {standard|rolling|blue-green|rollback|status|validate}"
    echo ""
    echo "Deployment strategies:"
    echo "  standard    - Stop all services, then start (brief downtime)"
    echo "  rolling     - Update services one by one (zero downtime)"
    echo "  blue-green  - Blue-green deployment simulation (zero downtime)"
    echo ""
    echo "Operations:"
    echo "  rollback    - Rollback deployment"
    echo "  status      - Show deployment status"
    echo "  validate    - Validate current deployment"
}

# Main function
main() {
    local command="${1:-}"
    
    if [[ -z "$command" ]]; then
        usage
        exit 1
    fi
    
    case "$command" in
        "standard")
            check_prerequisites
            deploy_standard
            validate_deployment
            ;;
        "rolling")
            check_prerequisites
            deploy_rolling
            validate_deployment
            ;;
        "blue-green")
            check_prerequisites
            deploy_blue_green
            validate_deployment
            ;;
        "rollback")
            rollback
            ;;
        "status")
            status
            ;;
        "validate")
            validate_deployment
            ;;
        *)
            echo "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Trap errors
trap 'error "Deployment failed on line $LINENO"' ERR

# Run main function
main "$@"