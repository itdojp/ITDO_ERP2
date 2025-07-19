#!/bin/bash

# Agent Integration Script for Multi-Environment Setup
# Purpose: Deploy and configure agents across multiple environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Agent configuration
AGENT_ENVIRONMENTS=("dev" "staging" "prod")
AGENT_PORT_BASE=9000

# Create agent configuration for each environment
create_agent_config() {
    local env_name=$1
    local port=$(( AGENT_PORT_BASE + $(echo "$env_name" | tr '[:lower:]' '[:upper:]' | sed 's/DEV/0/;s/STAGING/1/;s/PROD/2/') ))
    local config_dir="$PROJECT_ROOT/configs/$env_name"
    
    log "Creating agent configuration for $env_name environment..."
    
    # Create agent-specific configuration
    cat > "$config_dir/agent.env" << EOF
# Agent Configuration for $env_name
AGENT_NAME=itdo-agent-$env_name
AGENT_PORT=$port
AGENT_ENVIRONMENT=$env_name

# Database connections
DATABASE_URL=postgresql://postgres:postgres@localhost:$(grep DATABASE_URL "$config_dir/.env" | cut -d':' -f4 | cut -d'/' -f1)$(grep DATABASE_URL "$config_dir/.env" | cut -d'/' -f2-)
REDIS_URL=$(grep REDIS_URL "$config_dir/.env")

# Backend API endpoints
BACKEND_API_URL=http://$(grep BACKEND_HOST "$config_dir/.env" | cut -d'=' -f2):$(grep BACKEND_PORT "$config_dir/.env" | cut -d'=' -f2)

# Agent health check
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/itdo-agent-$env_name.log
EOF
    
    log "Created agent configuration for $env_name"
}

# Create agent health check script
create_health_check() {
    local env_name=$1
    local script_path="$PROJECT_ROOT/scripts/health-check-$env_name.sh"
    
    cat > "$script_path" << EOF
#!/bin/bash
# Health check script for $env_name environment

set -e

ENV_NAME="$env_name"
CONFIG_DIR="$PROJECT_ROOT/configs/$env_name"

# Source agent configuration
if [ -f "\$CONFIG_DIR/agent.env" ]; then
    source "\$CONFIG_DIR/agent.env"
else
    echo "Agent configuration not found for \$ENV_NAME"
    exit 1
fi

# Check agent process
check_agent_process() {
    if pgrep -f "itdo-agent-\$ENV_NAME" > /dev/null; then
        echo "Agent process is running for \$ENV_NAME"
        return 0
    else
        echo "Agent process is not running for \$ENV_NAME"
        return 1
    fi
}

# Check database connectivity
check_database() {
    if PGPASSWORD=postgres psql -h localhost -p \$(echo \$DATABASE_URL | cut -d':' -f4 | cut -d'/' -f1) -U postgres -d \$(echo \$DATABASE_URL | cut -d'/' -f2) -c "SELECT 1;" > /dev/null 2>&1; then
        echo "Database connection successful for \$ENV_NAME"
        return 0
    else
        echo "Database connection failed for \$ENV_NAME"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    local redis_port=\$(echo \$REDIS_URL | cut -d':' -f3 | cut -d'/' -f1)
    if redis-cli -p \$redis_port ping > /dev/null 2>&1; then
        echo "Redis connection successful for \$ENV_NAME"
        return 0
    else
        echo "Redis connection failed for \$ENV_NAME"
        return 1
    fi
}

# Check backend API
check_backend_api() {
    if curl -s -o /dev/null -w "%{http_code}" "\$BACKEND_API_URL/health" | grep -q "200"; then
        echo "Backend API is responding for \$ENV_NAME"
        return 0
    else
        echo "Backend API is not responding for \$ENV_NAME"
        return 1
    fi
}

# Main health check
main() {
    echo "=== Health Check for \$ENV_NAME Environment ==="
    echo "\$(date)"
    echo
    
    local status=0
    
    if ! check_agent_process; then
        status=1
    fi
    
    if ! check_database; then
        status=1
    fi
    
    if ! check_redis; then
        status=1
    fi
    
    if ! check_backend_api; then
        status=1
    fi
    
    if [ \$status -eq 0 ]; then
        echo "All health checks passed for \$ENV_NAME"
    else
        echo "Some health checks failed for \$ENV_NAME"
    fi
    
    exit \$status
}

main "\$@"
EOF
    
    chmod +x "$script_path"
    log "Created health check script for $env_name"
}

# Create agent deployment script
create_deployment_script() {
    local env_name=$1
    local script_path="$PROJECT_ROOT/scripts/deploy-agent-$env_name.sh"
    
    cat > "$script_path" << EOF
#!/bin/bash
# Deploy agent for $env_name environment

set -e

ENV_NAME="$env_name"
CONFIG_DIR="$PROJECT_ROOT/configs/$env_name"

echo "Deploying agent for \$ENV_NAME environment..."

# Source agent configuration
if [ -f "\$CONFIG_DIR/agent.env" ]; then
    source "\$CONFIG_DIR/agent.env"
else
    echo "Agent configuration not found for \$ENV_NAME"
    exit 1
fi

# Create log directory
mkdir -p "\$(dirname \$LOG_FILE)"

# Start agent process (simulated)
echo "Starting agent process for \$ENV_NAME..."
echo "Agent name: \$AGENT_NAME"
echo "Agent port: \$AGENT_PORT"
echo "Environment: \$AGENT_ENVIRONMENT"
echo "Database URL: \$DATABASE_URL"
echo "Redis URL: \$REDIS_URL"
echo "Backend API: \$BACKEND_API_URL"

# Create agent process simulation
nohup bash -c "
while true; do
    echo \"\$(date): Agent \$AGENT_NAME is running\" >> \$LOG_FILE
    sleep \$HEALTH_CHECK_INTERVAL
done
" > /dev/null 2>&1 &

echo \$! > "/tmp/itdo-agent-\$ENV_NAME.pid"

echo "Agent deployed successfully for \$ENV_NAME"
echo "PID: \$(cat /tmp/itdo-agent-\$ENV_NAME.pid)"
echo "Log file: \$LOG_FILE"
EOF
    
    chmod +x "$script_path"
    log "Created deployment script for $env_name"
}

# Create master deployment script
create_master_deployment() {
    cat > "$PROJECT_ROOT/scripts/deploy-all-agents.sh" << 'EOF'
#!/bin/bash
# Deploy all agents across environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENTS=("dev" "staging" "prod")

echo "Deploying agents across all environments..."

for env in "${ENVIRONMENTS[@]}"; do
    echo "Deploying agent for $env environment..."
    
    if [ -f "$SCRIPT_DIR/deploy-agent-$env.sh" ]; then
        bash "$SCRIPT_DIR/deploy-agent-$env.sh"
    else
        echo "Deployment script not found for $env"
    fi
    
    echo
done

echo "All agents deployed successfully!"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/deploy-all-agents.sh"
    log "Created master deployment script"
}

# Main function
main() {
    log "Starting agent integration setup..."
    
    # Create agent configurations for all environments
    for env in "${AGENT_ENVIRONMENTS[@]}"; do
        create_agent_config "$env"
        create_health_check "$env"
        create_deployment_script "$env"
    done
    
    # Create master deployment script
    create_master_deployment
    
    log "Agent integration setup completed!"
    echo
    echo -e "${GREEN}Agent Integration Summary:${NC}"
    echo "- Agent configurations created for all environments"
    echo "- Health check scripts: $PROJECT_ROOT/scripts/health-check-*.sh"
    echo "- Deployment scripts: $PROJECT_ROOT/scripts/deploy-agent-*.sh"
    echo "- Master deployment: $PROJECT_ROOT/scripts/deploy-all-agents.sh"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review agent configurations in configs/*/agent.env"
    echo "2. Run deployment scripts to start agents"
    echo "3. Use health check scripts to monitor agent status"
    echo "4. Integrate with backend API endpoints"
}

# Run main function
main "$@"