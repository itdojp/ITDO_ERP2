#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="$(basename "$(dirname "$SCRIPT_DIR")")"

echo "🛑 Stopping ITDO_ERP2 Agent for $ENV_NAME environment"

# Stop backend
if [ -f "/tmp/backend_${ENV_NAME}_pid" ]; then
    BACKEND_PID=$(cat "/tmp/backend_${ENV_NAME}_pid")
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "🛑 Stopping backend (PID: $BACKEND_PID)"
        kill "$BACKEND_PID"
        rm "/tmp/backend_${ENV_NAME}_pid"
    fi
fi

# Stop frontend
if [ -f "/tmp/frontend_${ENV_NAME}_pid" ]; then
    FRONTEND_PID=$(cat "/tmp/frontend_${ENV_NAME}_pid")
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "🛑 Stopping frontend (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID"
        rm "/tmp/frontend_${ENV_NAME}_pid"
    fi
fi

# Remove status file
rm -f "/tmp/agent_${ENV_NAME}_status.json"

echo "✅ Agent stopped for $ENV_NAME environment"
