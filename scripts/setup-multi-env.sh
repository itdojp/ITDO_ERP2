#!/bin/bash

# Multi-Environment Setup Script for Agent Verification
# Purpose: Create multiple isolated environments for agent testing

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/multi-env-setup.log"

# Environment Configuration
ENV_CONFIG=(
    "dev:172.20.10.2:8000:3000:5435:6382:itdo_erp_dev:0"
    "staging:172.20.10.3:8001:3001:5433:6380:itdo_erp_staging:1"
    "prod:172.20.10.4:8002:3002:5434:6381:itdo_erp_prod:2"
)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running on WSL or Linux
    if grep -q Microsoft /proc/version 2>/dev/null; then
        log "Running on WSL environment"
    else
        log "Running on Linux environment"
    fi
    
    # Check for required tools
    local required_tools=("podman" "ip" "ss")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "Required tool '$tool' is not installed"
            return 1
        fi
    done
    
    log "Prerequisites check passed"
    return 0
}

# Get current system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Check memory
    local total_mem=$(free -g | awk '/^Mem:/{print $2}')
    local available_mem=$(free -g | awk '/^Mem:/{print $7}')
    
    log "Total memory: ${total_mem}GB"
    log "Available memory: ${available_mem}GB"
    
    if [ "$available_mem" -lt 6 ]; then
        warning "Less than 6GB available memory. Performance may be affected."
    fi
    
    # Check CPU cores
    local cpu_cores=$(nproc)
    log "CPU cores: $cpu_cores"
    
    if [ "$cpu_cores" -lt 4 ]; then
        warning "Less than 4 CPU cores. Performance may be affected."
    fi
}

# Setup network configuration
setup_network() {
    log "Setting up network configuration..."
    
    # Get current base IP
    local base_ip=$(ip addr show eth0 | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+' | head -1)
    log "Current base IP: $base_ip"
    
    # Check if additional IPs are already configured
    for config in "${ENV_CONFIG[@]}"; do
        IFS=':' read -r env_name ip_addr backend_port frontend_port db_port redis_port db_name redis_db <<< "$config"
        
        if ip addr show eth0 | grep -q "$ip_addr"; then
            log "IP $ip_addr already configured"
        else
            log "Adding IP $ip_addr to eth0"
            # Attempt to add IP address (requires sudo)
            if sudo ip addr add "$ip_addr/20" dev eth0 2>>$LOG_FILE; then
                log "Successfully added IP $ip_addr"
            else
                warning "Failed to add IP $ip_addr - may require manual configuration"
                echo "# Manual command: sudo ip addr add $ip_addr/20 dev eth0" >> "$LOG_FILE"
            fi
        fi
    done
    
    # Verify network configuration
    log "Current network configuration:"
    ip addr show eth0 | grep inet | tee -a "$LOG_FILE"
    
    log "Network configuration completed"
}

# Check port availability
check_port_availability() {
    local port=$1
    if ss -tuln | grep -q ":$port "; then
        return 1
    fi
    return 0
}

# Create environment-specific configuration
create_env_config() {
    local env_name=$1
    local ip_addr=$2
    local backend_port=$3
    local frontend_port=$4
    local db_port=$5
    local redis_port=$6
    local db_name=$7
    local redis_db=$8
    
    local config_dir="$PROJECT_ROOT/configs/$env_name"
    mkdir -p "$config_dir"
    
    # Create .env file for this environment
    cat > "$config_dir/.env" << EOF
# Environment: $env_name
# IP Address: $ip_addr

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:$db_port/$db_name
REDIS_URL=redis://localhost:$redis_port/$redis_db

# Server Configuration
BACKEND_HOST=$ip_addr
BACKEND_PORT=$backend_port
FRONTEND_HOST=$ip_addr
FRONTEND_PORT=$frontend_port

# Development Mode
DEBUG=true
ENVIRONMENT=$env_name

# Authentication
JWT_SECRET_KEY=${env_name}_jwt_secret_$(date +%s)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://$ip_addr:$frontend_port"]
EOF
    
    log "Created configuration for $env_name environment"
}

# Create container startup script
create_container_script() {
    local env_name=$1
    local ip_addr=$2
    local backend_port=$3
    local frontend_port=$4
    local db_port=$5
    local redis_port=$6
    local db_name=$7
    local redis_db=$8
    
    local script_path="$PROJECT_ROOT/scripts/start-$env_name-env.sh"
    
    cat > "$script_path" << EOF
#!/bin/bash
# Start $env_name environment containers

set -e

ENV_NAME="$env_name"
IP_ADDR="$ip_addr"
CONFIG_DIR="$PROJECT_ROOT/configs/$env_name"

echo "Starting \$ENV_NAME environment..."

# Check if ports are available
if ss -tuln | grep -q ":$db_port "; then
    echo "Port $db_port is already in use"
    exit 1
fi

if ss -tuln | grep -q ":$redis_port "; then
    echo "Port $redis_port is already in use"
    exit 1
fi

# Start PostgreSQL
echo "Starting PostgreSQL for \$ENV_NAME..."
podman run -d \\
    --name "itdo-postgres-\$ENV_NAME" \\
    --network host \\
    -e POSTGRES_DB="$db_name" \\
    -e POSTGRES_USER=postgres \\
    -e POSTGRES_PASSWORD=postgres \\
    -v "\$CONFIG_DIR/postgres-data:/var/lib/postgresql/data" \\
    -p $ip_addr:$db_port:5432 \\
    postgres:15-alpine

# Start Redis
echo "Starting Redis for \$ENV_NAME..."
podman run -d \\
    --name "itdo-redis-\$ENV_NAME" \\
    --network host \\
    -p $ip_addr:$redis_port:6379 \\
    redis:7-alpine redis-server --appendonly yes

# Wait for services to be ready
sleep 10

echo "\$ENV_NAME environment started successfully!"
echo "PostgreSQL: $ip_addr:$db_port"
echo "Redis: $ip_addr:$redis_port"
echo "Backend will be available at: http://$ip_addr:$backend_port"
echo "Frontend will be available at: http://$ip_addr:$frontend_port"
EOF
    
    chmod +x "$script_path"
    log "Created startup script for $env_name environment"
}

# Create monitoring script
create_monitoring_script() {
    cat > "$PROJECT_ROOT/scripts/monitor-environments.sh" << 'EOF'
#!/bin/bash
# Monitor all environments

echo "=== Multi-Environment Status ==="
echo "$(date)"
echo

# Check container status
echo "Container Status:"
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

# Check network interfaces
echo "Network Interfaces:"
ip addr show eth0 | grep inet
echo

# Check port usage
echo "Port Usage:"
ss -tuln | grep -E ":(8000|8001|8002|3000|3001|3002|5432|5433|5434|6379|6380|6381) "
echo

# Check system resources
echo "System Resources:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/monitor-environments.sh"
    log "Created monitoring script"
}

# Create cleanup script
create_cleanup_script() {
    cat > "$PROJECT_ROOT/scripts/cleanup-environments.sh" << 'EOF'
#!/bin/bash
# Cleanup all environments

echo "Cleaning up all environments..."

# Stop and remove containers
for env in dev staging prod; do
    echo "Cleaning up $env environment..."
    podman stop "itdo-postgres-$env" 2>/dev/null || true
    podman stop "itdo-redis-$env" 2>/dev/null || true
    podman rm "itdo-postgres-$env" 2>/dev/null || true
    podman rm "itdo-redis-$env" 2>/dev/null || true
done

# Remove additional IP addresses (would need sudo in real environment)
echo "# sudo ip addr del 172.20.10.2/20 dev eth0" 
echo "# sudo ip addr del 172.20.10.3/20 dev eth0"
echo "# sudo ip addr del 172.20.10.4/20 dev eth0"

echo "Cleanup completed"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/cleanup-environments.sh"
    log "Created cleanup script"
}

# Main setup function
main() {
    log "Starting multi-environment setup..."
    
    # Initialize log file
    echo "Multi-Environment Setup Log - $(date)" > "$LOG_FILE"
    
    # Run setup steps
    if ! check_prerequisites; then
        error "Prerequisites check failed"
        exit 1
    fi
    
    check_system_resources
    setup_network
    
    # Create configurations for each environment
    for config in "${ENV_CONFIG[@]}"; do
        IFS=':' read -r env_name ip_addr backend_port frontend_port db_port redis_port db_name redis_db <<< "$config"
        
        log "Setting up $env_name environment..."
        
        # Check port availability
        for port in "$backend_port" "$frontend_port" "$db_port" "$redis_port"; do
            if ! check_port_availability "$port"; then
                warning "Port $port is already in use"
            fi
        done
        
        create_env_config "$env_name" "$ip_addr" "$backend_port" "$frontend_port" "$db_port" "$redis_port" "$db_name" "$redis_db"
        create_container_script "$env_name" "$ip_addr" "$backend_port" "$frontend_port" "$db_port" "$redis_port" "$db_name" "$redis_db"
    done
    
    # Create utility scripts
    create_monitoring_script
    create_cleanup_script
    
    log "Multi-environment setup completed successfully!"
    echo
    echo -e "${GREEN}Setup Summary:${NC}"
    echo "- Created 3 environment configurations (dev, staging, prod)"
    echo "- Environment configs: $PROJECT_ROOT/configs/"
    echo "- Start scripts: $PROJECT_ROOT/scripts/start-*-env.sh"
    echo "- Monitor script: $PROJECT_ROOT/scripts/monitor-environments.sh"
    echo "- Cleanup script: $PROJECT_ROOT/scripts/cleanup-environments.sh"
    echo "- Log file: $LOG_FILE"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review the generated configurations"
    echo "2. Run individual environment start scripts"
    echo "3. Use the monitoring script to check status"
    echo "4. Deploy agents to each environment"
    echo
    echo -e "${BLUE}Note:${NC} Network IP configuration requires sudo privileges in WSL"
}

# Run main function
main "$@"