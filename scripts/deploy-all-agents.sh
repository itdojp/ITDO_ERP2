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
