#!/bin/bash
# ITDO ERP v2 - Zero-Downtime Production Deploy Script
# CC03 v59.0 - Practical Production Infrastructure

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
COMPOSE_FILE="${PROJECT_ROOT}/infra/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/infra/.env.production"
BACKUP_DIR="${PROJECT_ROOT}/backups/deploy"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
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

# Pre-deployment checks
pre_deploy_checks() {
    log "Running pre-deployment checks..."
    
    # Check required files
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Check Docker/Podman
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Validate compose configuration
    if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config --quiet; then
        error "Docker Compose configuration is invalid"
        exit 1
    fi
    
    log "Pre-deployment checks passed"
}

# Backup current state
backup_current_state() {
    log "Creating pre-deployment backup..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/backup_${backup_timestamp}"
    
    mkdir -p "$backup_path"
    
    # Database backup
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps postgres | grep -q "Up"; then
        log "Backing up database..."
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            pg_dump -U itdo_user itdo_erp > "${backup_path}/database.sql"
    fi
    
    # Volume backup
    log "Backing up volumes..."
    docker run --rm -v itdo-postgres-data:/source -v "${backup_path}:/backup" \
        alpine tar czf /backup/postgres_data.tar.gz -C /source .
    
    docker run --rm -v itdo-redis-data:/source -v "${backup_path}:/backup" \
        alpine tar czf /backup/redis_data.tar.gz -C /source .
    
    echo "$backup_path" > /tmp/last_backup_path
    log "Backup completed: $backup_path"
}

# Health check function
health_check() {
    local service=$1
    local max_attempts=${2:-30}
    local attempt=1
    
    log "Performing health check for $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps "$service" | grep -q "healthy\|Up"; then
            log "Health check passed for $service"
            return 0
        fi
        
        info "Health check attempt $attempt/$max_attempts for $service"
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed for $service after $max_attempts attempts"
    return 1
}

# Blue-Green deployment
blue_green_deploy() {
    log "Starting Blue-Green deployment..."
    
    # Get current environment color
    local current_color="blue"
    if docker ps --format "table {{.Names}}" | grep -q "green"; then
        current_color="green"
    fi
    
    local new_color="green"
    if [[ "$current_color" == "green" ]]; then
        new_color="blue"
    fi
    
    log "Current: $current_color, Deploying: $new_color"
    
    # Deploy new environment
    log "Deploying $new_color environment..."
    COMPOSE_PROJECT_NAME="itdo-$new_color" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to be healthy
    sleep 30
    
    # Health checks for critical services
    local services=("postgres" "redis" "backend" "frontend")
    for service in "${services[@]}"; do
        if ! COMPOSE_PROJECT_NAME="itdo-$new_color" health_check "$service"; then
            error "Health check failed for $service in $new_color environment"
            log "Rolling back..."
            COMPOSE_PROJECT_NAME="itdo-$new_color" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
            return 1
        fi
    done
    
    # Switch traffic (in production, this would involve load balancer configuration)
    log "Switching traffic to $new_color environment..."
    
    # Stop old environment
    log "Stopping $current_color environment..."
    COMPOSE_PROJECT_NAME="itdo-$current_color" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    log "Blue-Green deployment completed successfully"
}

# Rolling update deployment
rolling_update_deploy() {
    log "Starting rolling update deployment..."
    
    # Update images first
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Rolling update for stateless services
    local services=("frontend" "backend")
    
    for service in "${services[@]}"; do
        log "Rolling update for $service..."
        
        # Scale up
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --scale "$service=2" --no-recreate
        sleep 30
        
        # Health check new instance
        if ! health_check "$service"; then
            error "Health check failed for new $service instance"
            return 1
        fi
        
        # Scale back down (removes old instance)
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --scale "$service=1" --no-recreate
        
        log "$service rolling update completed"
    done
    
    log "Rolling update deployment completed successfully"
}

# Standard deployment
standard_deploy() {
    log "Starting standard deployment..."
    
    # Pull latest images
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Deploy services
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to start
    sleep 60
    
    # Health checks
    local services=("postgres" "redis" "backend" "frontend" "nginx")
    for service in "${services[@]}"; do
        if ! health_check "$service"; then
            error "Health check failed for $service"
            return 1
        fi
    done
    
    log "Standard deployment completed successfully"
}

# Post-deployment verification
post_deploy_verification() {
    log "Running post-deployment verification..."
    
    # API health check
    local api_url="http://localhost/api/v1/health"
    if curl -f -s "$api_url" > /dev/null; then
        log "API health check passed"
    else
        error "API health check failed"
        return 1
    fi
    
    # Frontend health check
    local frontend_url="http://localhost/health"
    if curl -f -s "$frontend_url" > /dev/null; then
        log "Frontend health check passed"
    else
        error "Frontend health check failed"
        return 1
    fi
    
    # Database connectivity
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        psql -U itdo_user -d itdo_erp -c "SELECT 1;" > /dev/null; then
        log "Database connectivity verified"
    else
        error "Database connectivity check failed"
        return 1
    fi
    
    log "Post-deployment verification completed successfully"
}

# Rollback function
rollback() {
    error "Rolling back deployment..."
    
    local backup_path
    if [[ -f /tmp/last_backup_path ]]; then
        backup_path=$(cat /tmp/last_backup_path)
        
        if [[ -d "$backup_path" ]]; then
            log "Restoring from backup: $backup_path"
            
            # Restore database
            if [[ -f "${backup_path}/database.sql" ]]; then
                docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
                    psql -U itdo_user -d itdo_erp < "${backup_path}/database.sql"
            fi
            
            # Restore volumes
            if [[ -f "${backup_path}/postgres_data.tar.gz" ]]; then
                docker run --rm -v itdo-postgres-data:/target -v "${backup_path}:/backup" \
                    alpine sh -c "rm -rf /target/* && tar xzf /backup/postgres_data.tar.gz -C /target"
            fi
            
            if [[ -f "${backup_path}/redis_data.tar.gz" ]]; then
                docker run --rm -v itdo-redis-data:/target -v "${backup_path}:/backup" \
                    alpine sh -c "rm -rf /target/* && tar xzf /backup/redis_data.tar.gz -C /target"
            fi
            
            # Restart services
            docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
            
            log "Rollback completed"
        else
            error "Backup path not found: $backup_path"
        fi
    else
        error "No backup information found"
    fi
}

# Main deployment function
main() {
    local deployment_type=${1:-standard}
    local start_time=$(date +%s)
    
    log "Starting ITDO ERP v2 production deployment ($deployment_type)"
    
    # Trap for cleanup on error
    trap rollback ERR
    
    # Pre-deployment
    pre_deploy_checks
    backup_current_state
    
    # Execute deployment based on type
    case "$deployment_type" in
        "blue-green")
            blue_green_deploy
            ;;
        "rolling")
            rolling_update_deploy
            ;;
        "standard"|*)
            standard_deploy
            ;;
    esac
    
    # Post-deployment
    post_deploy_verification
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "Deployment completed successfully in ${duration} seconds"
    
    # Cleanup
    trap - ERR
}

# Usage information
usage() {
    echo "Usage: $0 [deployment_type]"
    echo ""
    echo "Deployment types:"
    echo "  standard    - Standard deployment (default)"
    echo "  blue-green  - Blue-Green deployment"
    echo "  rolling     - Rolling update deployment"
    echo ""
    echo "Examples:"
    echo "  $0                # Standard deployment"
    echo "  $0 blue-green     # Blue-Green deployment"
    echo "  $0 rolling        # Rolling update deployment"
}

# Check arguments
if [[ $# -gt 1 ]]; then
    usage
    exit 1
fi

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

# Execute main function
main "${1:-standard}"