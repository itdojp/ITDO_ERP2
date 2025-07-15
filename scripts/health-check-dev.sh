#!/bin/bash
# Health check script for dev environment

set -e

ENV_NAME="dev"
CONFIG_DIR="/home/work/ITDO_ERP2/configs/dev"

# Source agent configuration
if [ -f "$CONFIG_DIR/agent.env" ]; then
    source "$CONFIG_DIR/agent.env"
else
    echo "Agent configuration not found for $ENV_NAME"
    exit 1
fi

# Check agent process
check_agent_process() {
    if pgrep -f "itdo-agent-$ENV_NAME" > /dev/null; then
        echo "Agent process is running for $ENV_NAME"
        return 0
    else
        echo "Agent process is not running for $ENV_NAME"
        return 1
    fi
}

# Check database connectivity
check_database() {
    if PGPASSWORD=postgres psql -h localhost -p $(echo $DATABASE_URL | cut -d':' -f4 | cut -d'/' -f1) -U postgres -d $(echo $DATABASE_URL | cut -d'/' -f2) -c "SELECT 1;" > /dev/null 2>&1; then
        echo "Database connection successful for $ENV_NAME"
        return 0
    else
        echo "Database connection failed for $ENV_NAME"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    local redis_port=$(echo $REDIS_URL | cut -d':' -f3 | cut -d'/' -f1)
    if redis-cli -p $redis_port ping > /dev/null 2>&1; then
        echo "Redis connection successful for $ENV_NAME"
        return 0
    else
        echo "Redis connection failed for $ENV_NAME"
        return 1
    fi
}

# Check backend API
check_backend_api() {
    if curl -s -o /dev/null -w "%{http_code}" "$BACKEND_API_URL/health" | grep -q "200"; then
        echo "Backend API is responding for $ENV_NAME"
        return 0
    else
        echo "Backend API is not responding for $ENV_NAME"
        return 1
    fi
}

# Main health check
main() {
    echo "=== Health Check for $ENV_NAME Environment ==="
    echo "$(date)"
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
    
    if [ $status -eq 0 ]; then
        echo "All health checks passed for $ENV_NAME"
    else
        echo "Some health checks failed for $ENV_NAME"
    fi
    
    exit $status
}

main "$@"
