#!/bin/bash

# Test Environment Startup Script
# Purpose: Test individual environment startup and validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Test environment startup
test_environment() {
    local env_name=$1
    local script_path="$PROJECT_ROOT/scripts/start-$env_name-env.sh"
    
    log "Testing $env_name environment startup..."
    
    if [ ! -f "$script_path" ]; then
        error "Startup script not found: $script_path"
        return 1
    fi
    
    # Check if script is executable
    if [ ! -x "$script_path" ]; then
        log "Making script executable: $script_path"
        chmod +x "$script_path"
    fi
    
    # Test script execution (dry run)
    log "Running $env_name environment startup script..."
    
    # Execute the script
    if bash "$script_path"; then
        log "$env_name environment started successfully"
        
        # Wait for services to be ready
        sleep 15
        
        # Check if containers are running
        local postgres_container="itdo-postgres-$env_name"
        local redis_container="itdo-redis-$env_name"
        
        if podman ps | grep -q "$postgres_container"; then
            log "PostgreSQL container is running for $env_name"
        else
            warning "PostgreSQL container not running for $env_name"
        fi
        
        if podman ps | grep -q "$redis_container"; then
            log "Redis container is running for $env_name"
        else
            warning "Redis container not running for $env_name"
        fi
        
        return 0
    else
        error "Failed to start $env_name environment"
        return 1
    fi
}

# Test all environments
test_all_environments() {
    log "Testing all environment startups..."
    
    local environments=("dev" "staging" "prod")
    local success_count=0
    
    for env in "${environments[@]}"; do
        if test_environment "$env"; then
            ((success_count++))
        fi
        echo
    done
    
    log "Successfully started $success_count/${#environments[@]} environments"
    
    if [ $success_count -eq ${#environments[@]} ]; then
        log "All environments started successfully!"
        return 0
    else
        warning "Some environments failed to start"
        return 1
    fi
}

# Cleanup function
cleanup_environments() {
    log "Cleaning up test environments..."
    
    local environments=("dev" "staging" "prod")
    
    for env in "${environments[@]}"; do
        log "Stopping $env environment containers..."
        podman stop "itdo-postgres-$env" 2>/dev/null || true
        podman stop "itdo-redis-$env" 2>/dev/null || true
        podman rm "itdo-postgres-$env" 2>/dev/null || true
        podman rm "itdo-redis-$env" 2>/dev/null || true
    done
    
    log "Cleanup completed"
}

# Main execution
main() {
    log "Starting environment startup test..."
    
    # Option parsing
    case "${1:-test}" in
        "test")
            test_all_environments
            ;;
        "cleanup")
            cleanup_environments
            ;;
        "dev"|"staging"|"prod")
            test_environment "$1"
            ;;
        *)
            echo "Usage: $0 [test|cleanup|dev|staging|prod]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"