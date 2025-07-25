#!/bin/bash
# CC03 v64.0 - Blue-Green Deployment Implementation
# 即効性重視のインフラ改善 - Option A

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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_COMPOSE_FILE="compose-prod.yaml"
BLUE_COMPOSE_FILE="compose-blue.yaml"
GREEN_COMPOSE_FILE="compose-green.yaml"
ENV_FILE=".env.prod"
CURRENT_ENV_FILE=".env.current"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_TIMEOUT=60

# State management
CURRENT_ENVIRONMENT=""
TARGET_ENVIRONMENT=""
NGINX_CONFIG_DIR="nginx"
BACKUP_DIR="blue-green-backups"

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
    echo "========================================================"
    echo "🔄 CC03 v64.0 Blue-Green Deployment System"
    echo "   Zero-Downtime Production Deployment Solution"
    echo "========================================================"
    echo -e "${NC}"
    echo "🎯 Features:"
    echo "  • Zero-downtime deployments"
    echo "  • Instant rollback capability"
    echo "  • Health check validation"
    echo "  • Traffic switching with NGINX"
    echo "  • Automatic backup before deployment"
    echo "  • Safe production updates"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log "Checking Blue-Green deployment prerequisites..."
    
    # Check if running from correct directory
    if [[ ! -f "$BASE_COMPOSE_FILE" ]]; then
        error "Must run from infra/ directory. $BASE_COMPOSE_FILE not found."
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
        error "Production environment file $ENV_FILE not found"
    fi
    
    # Check curl for health checks
    if ! command -v curl &> /dev/null; then
        error "curl is required for health checks"
    fi
    
    success "Prerequisites check completed"
}

# Initialize Blue-Green environment
initialize_blue_green() {
    log "Initializing Blue-Green deployment environment..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Generate Blue and Green compose files if they don't exist
    if [[ ! -f "$BLUE_COMPOSE_FILE" ]] || [[ ! -f "$GREEN_COMPOSE_FILE" ]]; then
        generate_blue_green_configs
    fi
    
    # Create NGINX configuration templates
    create_nginx_templates
    
    # Determine current environment
    detect_current_environment
    
    success "Blue-Green environment initialized"
}

# Generate Blue and Green Docker Compose configurations
generate_blue_green_configs() {
    log "Generating Blue and Green compose configurations..."
    
    # Read base compose file and modify for Blue environment
    sed 's/container_name: \([^-]*\)/container_name: \1-blue/g' "$BASE_COMPOSE_FILE" > "$BLUE_COMPOSE_FILE"
    sed -i 's/- "80:80"/- "8080:80"/g' "$BLUE_COMPOSE_FILE"
    sed -i 's/- "443:443"/- "8443:443"/g' "$BLUE_COMPOSE_FILE"
    sed -i 's/- "3000:3000"/- "3001:3000"/g' "$BLUE_COMPOSE_FILE"
    sed -i 's/- "8000:8000"/- "8001:8000"/g' "$BLUE_COMPOSE_FILE"
    
    # Read base compose file and modify for Green environment
    sed 's/container_name: \([^-]*\)/container_name: \1-green/g' "$BASE_COMPOSE_FILE" > "$GREEN_COMPOSE_FILE"
    sed -i 's/- "80:80"/- "9080:80"/g' "$GREEN_COMPOSE_FILE"
    sed -i 's/- "443:443"/- "9443:443"/g' "$GREEN_COMPOSE_FILE"
    sed -i 's/- "3000:3000"/- "3002:3000"/g' "$GREEN_COMPOSE_FILE"
    sed -i 's/- "8000:8000"/- "8002:8000"/g' "$GREEN_COMPOSE_FILE"
    
    info "Blue environment ports: Frontend(3001), Backend(8001), NGINX(8080/8443)"
    info "Green environment ports: Frontend(3002), Backend(8002), NGINX(9080/9443)"
    
    success "Blue and Green configurations generated"
}

# Create NGINX configuration templates
create_nginx_templates() {
    log "Creating NGINX configuration templates..."
    
    mkdir -p "$NGINX_CONFIG_DIR/templates"
    
    # Blue environment NGINX config
    cat > "$NGINX_CONFIG_DIR/templates/nginx-blue.conf" << 'EOF'
# Blue Environment NGINX Configuration
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Upstream definitions for Blue environment
    upstream backend_blue {
        server backend-blue:8000;
    }
    
    upstream frontend_blue {
        server frontend-blue:3000;
    }
    
    # Main server block for Blue
    server {
        listen 80;
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/itdo-erp.com.crt;
        ssl_certificate_key /etc/nginx/ssl/itdo-erp.com.key;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "blue-healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend_blue;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Frontend application
        location / {
            proxy_pass http://frontend_blue;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

    # Green environment NGINX config
    cat > "$NGINX_CONFIG_DIR/templates/nginx-green.conf" << 'EOF'
# Green Environment NGINX Configuration
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Upstream definitions for Green environment
    upstream backend_green {
        server backend-green:8000;
    }
    
    upstream frontend_green {
        server frontend-green:3000;
    }
    
    # Main server block for Green
    server {
        listen 80;
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/itdo-erp.com.crt;
        ssl_certificate_key /etc/nginx/ssl/itdo-erp.com.key;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "green-healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend_green;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Frontend application
        location / {
            proxy_pass http://frontend_green;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

    # Main production NGINX config with routing
    cat > "$NGINX_CONFIG_DIR/templates/nginx-production.conf" << 'EOF'
# Production NGINX Configuration with Blue-Green Routing
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Upstream definitions - will be dynamically updated
    upstream backend_production {
        server 127.0.0.1:8001;  # Default to Blue
    }
    
    upstream frontend_production {
        server 127.0.0.1:3001;  # Default to Blue
    }
    
    # Main production server
    server {
        listen 80;
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/itdo-erp.com.crt;
        ssl_certificate_key /etc/nginx/ssl/itdo-erp.com.key;
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "production-healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Blue-Green deployment management
        location /deployment-status {
            access_log off;
            return 200 "active-environment: blue\n";
            add_header Content-Type text/plain;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend_production;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Health check headers
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }
        
        # Frontend application
        location / {
            proxy_pass http://frontend_production;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Health check headers
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }
    }
}
EOF

    success "NGINX configuration templates created"
}

# Detect current active environment
detect_current_environment() {
    log "Detecting current active environment..."
    
    if [[ -f "$CURRENT_ENV_FILE" ]]; then
        CURRENT_ENVIRONMENT=$(cat "$CURRENT_ENV_FILE")
        info "Current active environment: $CURRENT_ENVIRONMENT"
    else
        # Check if any environment is running
        if $COMPOSE_CMD -f "$BLUE_COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "Up"; then
            CURRENT_ENVIRONMENT="blue"
        elif $COMPOSE_CMD -f "$GREEN_COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "Up"; then
            CURRENT_ENVIRONMENT="green"
        else
            CURRENT_ENVIRONMENT="none"
            info "No active environment detected - this will be initial deployment"
        fi
        echo "$CURRENT_ENVIRONMENT" > "$CURRENT_ENV_FILE"
    fi
    
    # Determine target environment
    if [[ "$CURRENT_ENVIRONMENT" == "blue" ]]; then
        TARGET_ENVIRONMENT="green"
    else
        TARGET_ENVIRONMENT="blue"
    fi
    
    info "Target deployment environment: $TARGET_ENVIRONMENT"
}

# Perform health check on environment
health_check() {
    local environment=$1
    local max_attempts=30
    local attempt=1
    
    log "Performing health check on $environment environment..."
    
    # Determine ports based on environment
    if [[ "$environment" == "blue" ]]; then
        local backend_port=8001
        local frontend_port=3001
        local nginx_port=8080
    else
        local backend_port=8002
        local frontend_port=3002
        local nginx_port=9080
    fi
    
    while [[ $attempt -le $max_attempts ]]; do
        info "Health check attempt $attempt/$max_attempts"
        
        # Check backend health
        if curl -f -s "http://localhost:${backend_port}/api/v1/health" > /dev/null; then
            success "Backend health check passed"
            
            # Check frontend health
            if curl -f -s "http://localhost:${frontend_port}/" > /dev/null; then
                success "Frontend health check passed"
                
                # Check NGINX health
                if curl -f -s "http://localhost:${nginx_port}/health" > /dev/null; then
                    success "$environment environment is healthy"
                    return 0
                fi
            fi
        fi
        
        warn "Health check failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    error "$environment environment health check failed after $max_attempts attempts"
    return 1
}

# Deploy to target environment
deploy_to_environment() {
    local environment=$1
    
    log "Deploying to $environment environment..."
    
    # Determine compose file
    local compose_file
    if [[ "$environment" == "blue" ]]; then
        compose_file="$BLUE_COMPOSE_FILE"
    else
        compose_file="$GREEN_COMPOSE_FILE"
    fi
    
    # Pull latest images
    info "Pulling latest container images..."
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" pull
    
    # Stop existing services in target environment
    info "Stopping existing services in $environment environment..."
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" down --remove-orphans || true
    
    # Deploy to target environment
    info "Starting services in $environment environment..."
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" up -d
    
    # Wait for services to start
    info "Waiting for services to initialize..."
    sleep 60
    
    # Perform health check
    if health_check "$environment"; then
        success "$environment environment deployment successful"
        return 0
    else
        error "$environment environment deployment failed health check"
        return 1
    fi
}

# Switch traffic to target environment
switch_traffic() {
    local target_env=$1
    
    log "Switching traffic to $target_env environment..."
    
    # Create backup of current NGINX config
    if [[ -f "$NGINX_CONFIG_DIR/nginx-prod.conf" ]]; then
        cp "$NGINX_CONFIG_DIR/nginx-prod.conf" "$BACKUP_DIR/nginx-backup-$(date +%Y%m%d_%H%M%S).conf"
    fi
    
    # Update NGINX upstream configuration
    if [[ "$target_env" == "blue" ]]; then
        sed -i 's/server 127.0.0.1:800[12];/server 127.0.0.1:8001;/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
        sed -i 's/server 127.0.0.1:300[12];/server 127.0.0.1:3001;/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
        sed -i 's/active-environment: [a-z]*/active-environment: blue/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
    else
        sed -i 's/server 127.0.0.1:800[12];/server 127.0.0.1:8002;/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
        sed -i 's/server 127.0.0.1:300[12];/server 127.0.0.1:3002;/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
        sed -i 's/active-environment: [a-z]*/active-environment: green/g' "$NGINX_CONFIG_DIR/templates/nginx-production.conf"
    fi
    
    # Copy updated config to active location
    cp "$NGINX_CONFIG_DIR/templates/nginx-production.conf" "$NGINX_CONFIG_DIR/nginx-prod.conf"
    
    # Reload NGINX if it's running
    if $CONTAINER_ENGINE ps | grep -q nginx; then
        info "Reloading NGINX configuration..."
        $CONTAINER_ENGINE exec nginx nginx -s reload || warn "NGINX reload failed"
    fi
    
    # Update current environment tracking
    echo "$target_env" > "$CURRENT_ENV_FILE"
    
    # Final health check through main NGINX
    sleep 5
    if curl -f -s "http://localhost/health" > /dev/null; then
        success "Traffic successfully switched to $target_env environment"
        return 0
    else
        error "Traffic switch verification failed"
        return 1
    fi
}

# Rollback to previous environment
rollback() {
    log "Performing rollback to previous environment..."
    
    local previous_env
    if [[ "$CURRENT_ENVIRONMENT" == "blue" ]]; then
        previous_env="green"
    else
        previous_env="blue"
    fi
    
    warn "Rolling back from $CURRENT_ENVIRONMENT to $previous_env"
    
    # Check if previous environment is still running
    local compose_file
    if [[ "$previous_env" == "blue" ]]; then
        compose_file="$BLUE_COMPOSE_FILE"
    else
        compose_file="$GREEN_COMPOSE_FILE"
    fi
    
    if ! $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" ps | grep -q "Up"; then
        warn "Previous environment ($previous_env) is not running. Starting it..."
        $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" up -d
        sleep 30
    fi
    
    # Perform health check on previous environment
    if health_check "$previous_env"; then
        # Switch traffic back
        if switch_traffic "$previous_env"; then
            success "Rollback to $previous_env environment completed successfully"
            return 0
        fi
    fi
    
    error "Rollback failed"
    return 1
}

# Cleanup old environment
cleanup_old_environment() {
    local old_env=$1
    
    log "Cleaning up $old_env environment..."
    
    local compose_file
    if [[ "$old_env" == "blue" ]]; then
        compose_file="$BLUE_COMPOSE_FILE"
    else
        compose_file="$GREEN_COMPOSE_FILE"
    fi
    
    # Stop and remove containers
    $COMPOSE_CMD -f "$compose_file" --env-file "$ENV_FILE" down --remove-orphans
    
    success "$old_env environment cleaned up"
}

# Create deployment backup
create_deployment_backup() {
    log "Creating deployment backup..."
    
    local backup_name="blue-green-backup-$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup current environment state
    echo "$CURRENT_ENVIRONMENT" > "$backup_path/current_environment"
    
    # Backup NGINX configs
    cp -r "$NGINX_CONFIG_DIR" "$backup_path/" 2>/dev/null || true
    
    # Backup Docker compose states
    $COMPOSE_CMD -f "$BLUE_COMPOSE_FILE" --env-file "$ENV_FILE" ps > "$backup_path/blue_status.txt" 2>/dev/null || true
    $COMPOSE_CMD -f "$GREEN_COMPOSE_FILE" --env-file "$ENV_FILE" ps > "$backup_path/green_status.txt" 2>/dev/null || true
    
    success "Deployment backup created: $backup_path"
}

# Show deployment status
show_status() {
    echo -e "${PURPLE}"
    echo "🔄 Blue-Green Deployment Status"
    echo "==============================="
    echo -e "${NC}"
    
    echo -e "${BLUE}Current Environment:${NC} $CURRENT_ENVIRONMENT"
    echo -e "${BLUE}Target Environment:${NC} $TARGET_ENVIRONMENT"
    echo ""
    
    echo -e "${BLUE}=== Blue Environment Status ===${NC}"
    if $COMPOSE_CMD -f "$BLUE_COMPOSE_FILE" --env-file "$ENV_FILE" ps 2>/dev/null; then
        echo ""
    else
        echo "Blue environment not deployed"
    fi
    
    echo -e "${BLUE}=== Green Environment Status ===${NC}"
    if $COMPOSE_CMD -f "$GREEN_COMPOSE_FILE" --env-file "$ENV_FILE" ps 2>/dev/null; then
        echo ""
    else
        echo "Green environment not deployed"
    fi
    
    echo -e "${BLUE}=== Health Check URLs ===${NC}"
    echo "🔵 Blue Environment:"
    echo "   Frontend: http://localhost:3001"
    echo "   Backend: http://localhost:8001/api/v1/health"
    echo "   NGINX: http://localhost:8080/health"
    echo ""
    echo "🟢 Green Environment:"
    echo "   Frontend: http://localhost:3002"
    echo "   Backend: http://localhost:8002/api/v1/health"
    echo "   NGINX: http://localhost:9080/health"
    echo ""
    echo "🎯 Production Traffic:"
    echo "   Main Site: http://localhost"
    echo "   Status: http://localhost/deployment-status"
}

# Main function
main() {
    case ${1:-deploy} in
        "deploy")
            print_header
            check_prerequisites
            initialize_blue_green
            create_deployment_backup
            
            if deploy_to_environment "$TARGET_ENVIRONMENT"; then
                if switch_traffic "$TARGET_ENVIRONMENT"; then
                    success "🎉 Blue-Green deployment completed successfully!"
                    info "Active environment: $TARGET_ENVIRONMENT"
                    info "Previous environment: $CURRENT_ENVIRONMENT (kept running for rollback)"
                    echo ""
                    echo "💡 Next steps:"
                    echo "  • Monitor application performance"
                    echo "  • Run: $0 cleanup to remove old environment"
                    echo "  • Run: $0 rollback if issues are detected"
                else
                    error "Traffic switch failed. Attempting rollback..."
                    rollback
                fi
            else
                error "Deployment to $TARGET_ENVIRONMENT failed"
                exit 1
            fi
            ;;
        "rollback")
            print_header
            check_prerequisites
            detect_current_environment
            rollback
            ;;
        "cleanup")
            check_prerequisites
            detect_current_environment
            if [[ "$CURRENT_ENVIRONMENT" == "blue" ]]; then
                cleanup_old_environment "green"
            else
                cleanup_old_environment "blue"
            fi
            ;;
        "status")
            check_prerequisites
            detect_current_environment
            show_status
            ;;
        "switch")
            if [[ -n ${2:-} ]]; then
                check_prerequisites
                detect_current_environment
                if [[ "$2" == "blue" ]] || [[ "$2" == "green" ]]; then
                    switch_traffic "$2"
                else
                    error "Invalid environment. Use 'blue' or 'green'"
                fi
            else
                error "Specify environment: $0 switch [blue|green]"
            fi
            ;;
        "health")
            check_prerequisites
            detect_current_environment
            if [[ -n ${2:-} ]]; then
                health_check "$2"
            else
                health_check "$CURRENT_ENVIRONMENT"
            fi
            ;;
        "init")
            print_header
            check_prerequisites
            initialize_blue_green
            success "Blue-Green deployment system initialized"
            ;;
        "help")
            echo "Usage: $0 [deploy|rollback|cleanup|status|switch|health|init|help]"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy to inactive environment and switch traffic"
            echo "  rollback - Rollback to previous environment"
            echo "  cleanup  - Remove inactive environment"
            echo "  status   - Show current deployment status"
            echo "  switch   - Switch traffic to specified environment"
            echo "  health   - Check health of specified environment"
            echo "  init     - Initialize Blue-Green deployment system"
            echo "  help     - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy           # Deploy new version with zero downtime"
            echo "  $0 status           # Check current deployment status"
            echo "  $0 rollback         # Rollback to previous version"
            echo "  $0 switch blue      # Switch traffic to blue environment"
            echo "  $0 health green     # Check green environment health"
            echo "  $0 cleanup          # Remove inactive environment"
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Script execution
main "$@"