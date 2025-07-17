#!/bin/bash

# Agent startup script for environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="$(basename "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$SCRIPT_DIR/agent-config.json"

echo "🤖 Starting ITDO_ERP2 Agent for $ENV_NAME environment"

# Load configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Extract IP from config
HOST_IP=$(grep -o '"host_ip": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4)
echo "🌐 Agent will bind to IP: $HOST_IP"

# Check if IP is configured
if ! ip addr show dev eth0 | grep -q "$HOST_IP"; then
    echo "❌ IP $HOST_IP is not configured on eth0"
    exit 1
fi

# Set environment variables from config
export ITDO_ERP_ENV="$ENV_NAME"
export ITDO_ERP_HOST_IP="$HOST_IP"
export DATABASE_URL="postgresql://postgres:postgres@$HOST_IP:5432/itdo_erp_$ENV_NAME"
export REDIS_URL="redis://$HOST_IP:6379/0"
export KEYCLOAK_URL="http://$HOST_IP:8080"

# Change to project root
cd "$(dirname "$SCRIPT_DIR")/../../../"

# Start backend (if not already running)
if ! curl -s "http://$HOST_IP:8000/health" > /dev/null 2>&1; then
    echo "🚀 Starting backend on $HOST_IP:8000"
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "📦 Creating Python virtual environment"
        python3 -m venv .venv
    fi
    
    # Activate virtual environment and install dependencies
    source .venv/bin/activate
    if [ ! -f ".deps_installed" ]; then
        echo "📦 Installing dependencies"
        pip install -r requirements.txt
        touch .deps_installed
    fi
    
    # Run database migrations
    echo "🗄️  Running database migrations"
    alembic upgrade head
    
    # Start FastAPI server
    echo "🚀 Starting FastAPI server"
    uvicorn app.main:app --host "$HOST_IP" --port 8000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > "/tmp/backend_${ENV_NAME}_pid"
    
    cd ..
else
    echo "✅ Backend already running on $HOST_IP:8000"
fi

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s "http://$HOST_IP:8000/health" > /dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start after 60 seconds"
        exit 1
    fi
done

# Start frontend (if not already running)
if ! curl -s "http://$HOST_IP:3000" > /dev/null 2>&1; then
    echo "🌐 Starting frontend on $HOST_IP:3000"
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies"
        npm install
    fi
    
    # Set frontend environment variables
    export REACT_APP_API_URL="http://$HOST_IP:8000"
    export REACT_APP_ENVIRONMENT="$ENV_NAME"
    
    # Start development server
    npm start -- --host "$HOST_IP" --port 3000 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "/tmp/frontend_${ENV_NAME}_pid"
    
    cd ..
else
    echo "✅ Frontend already running on $HOST_IP:3000"
fi

# Create agent status file
cat > "/tmp/agent_${ENV_NAME}_status.json" << AGENT_EOF
{
  "environment": "$ENV_NAME",
  "host_ip": "$HOST_IP",
  "status": "running",
  "started_at": "$(date -Iseconds)",
  "backend_url": "http://$HOST_IP:8000",
  "frontend_url": "http://$HOST_IP:3000",
  "health_check": "http://$HOST_IP:8000/health"
}
AGENT_EOF

echo "✅ Agent deployment completed for $ENV_NAME environment"
echo "🌐 Access URLs:"
echo "   Backend API: http://$HOST_IP:8000"
echo "   Frontend: http://$HOST_IP:3000"
echo "   Health Check: http://$HOST_IP:8000/health"
