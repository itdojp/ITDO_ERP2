#!/bin/bash
# Deploy agent for prod environment

set -e

ENV_NAME="prod"
CONFIG_DIR="/home/work/ITDO_ERP2/configs/prod"

echo "Deploying agent for $ENV_NAME environment..."

# Source agent configuration
if [ -f "$CONFIG_DIR/agent.env" ]; then
    source "$CONFIG_DIR/agent.env"
else
    echo "Agent configuration not found for $ENV_NAME"
    exit 1
fi

# Create log directory
mkdir -p "$(dirname $LOG_FILE)"

# Start agent process (simulated)
echo "Starting agent process for $ENV_NAME..."
echo "Agent name: $AGENT_NAME"
echo "Agent port: $AGENT_PORT"
echo "Environment: $AGENT_ENVIRONMENT"
echo "Database URL: $DATABASE_URL"
echo "Redis URL: $REDIS_URL"
echo "Backend API: $BACKEND_API_URL"

# Create agent process simulation
nohup bash -c "
while true; do
    echo \"$(date): Agent $AGENT_NAME is running\" >> $LOG_FILE
    sleep $HEALTH_CHECK_INTERVAL
done
" > /dev/null 2>&1 &

echo $! > "/tmp/itdo-agent-$ENV_NAME.pid"

echo "Agent deployed successfully for $ENV_NAME"
echo "PID: $(cat /tmp/itdo-agent-$ENV_NAME.pid)"
echo "Log file: $LOG_FILE"
