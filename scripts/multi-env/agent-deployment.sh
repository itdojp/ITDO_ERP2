#!/bin/bash

# Agent Deployment Script for Multi-Environment Setup
# Implements Issue #147: Agent deployment across multiple verification environments

set -e

# Configuration
BASE_IP="172.23.14"
DEV_IP="${BASE_IP}.204"
STAGING_IP="${BASE_IP}.205"
PROD_IP="${BASE_IP}.206"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🤖 ITDO_ERP2 Agent Deployment${NC}"
echo "================================"

# Function to deploy agent to specific environment
deploy_agent() {
    local env_name=$1
    local ip=$2
    local agent_version=${3:-"latest"}
    
    echo -e "\n${BLUE}🚀 Deploying agent to ${env_name} environment (${ip})${NC}"
    
    # Create agent-specific directory
    local agent_dir="scripts/multi-env/agents/${env_name}"
    mkdir -p "$agent_dir"
    
    # Create agent configuration
    cat > "$agent_dir/agent-config.json" << EOF
{
  "environment": "${env_name}",
  "agent_id": "CC01-${env_name}",
  "network": {
    "host_ip": "${ip}",
    "backend_port": 8000,
    "frontend_port": 3000,
    "api_base_url": "http://${ip}:8000"
  },
  "database": {
    "host": "${ip}",
    "port": 5432,
    "database": "itdo_erp_${env_name}",
    "user": "postgres",
    "password": "postgres"
  },
  "redis": {
    "host": "${ip}",
    "port": 6379,
    "database": 0
  },
  "keycloak": {
    "host": "${ip}",
    "port": 8080,
    "realm": "itdo-erp-${env_name}",
    "base_url": "http://${ip}:8080"
  },
  "features": {
    "phase4_financial": true,
    "phase5_crm": true,
    "phase6_workflow": true,
    "phase7_analytics": true
  },
  "performance": {
    "max_memory_mb": 2048,
    "max_cpu_percent": 50,
    "request_timeout_seconds": 30
  },
  "monitoring": {
    "health_check_interval": 60,
    "log_level": "${env_name}" == "production" ? "INFO" : "DEBUG",
    "metrics_enabled": true
  }
}
EOF

    # Create agent startup script
    cat > "$agent_dir/start-agent.sh" << 'EOF'
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
EOF

    chmod +x "$agent_dir/start-agent.sh"
    
    # Create agent stop script
    cat > "$agent_dir/stop-agent.sh" << 'EOF'
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
EOF

    chmod +x "$agent_dir/stop-agent.sh"
    
    echo -e "${GREEN}✅ Agent deployment configuration created for ${env_name}${NC}"
}

# Function to create master agent controller
create_agent_controller() {
    cat > "scripts/multi-env/agent-controller.sh" << 'EOF'
#!/bin/bash

# Master Agent Controller for Multi-Environment Setup
# Controls all agent instances across development, staging, and production

set -e

ENVIRONMENTS=("development" "staging" "production")
ACTION=${1:-"status"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🎛️  ITDO_ERP2 Agent Controller${NC}"
echo "=============================="

case "$ACTION" in
    "start")
        echo -e "${BLUE}🚀 Starting all agent environments${NC}"
        for env in "${ENVIRONMENTS[@]}"; do
            echo -e "\n${YELLOW}Starting $env environment...${NC}"
            if [ -f "scripts/multi-env/agents/$env/start-agent.sh" ]; then
                ./scripts/multi-env/agents/$env/start-agent.sh
            else
                echo -e "${RED}❌ Start script not found for $env${NC}"
            fi
        done
        ;;
    
    "stop")
        echo -e "${BLUE}🛑 Stopping all agent environments${NC}"
        for env in "${ENVIRONMENTS[@]}"; do
            echo -e "\n${YELLOW}Stopping $env environment...${NC}"
            if [ -f "scripts/multi-env/agents/$env/stop-agent.sh" ]; then
                ./scripts/multi-env/agents/$env/stop-agent.sh
            else
                echo -e "${RED}❌ Stop script not found for $env${NC}"
            fi
        done
        ;;
    
    "status")
        echo -e "${BLUE}📊 Agent Status Report${NC}"
        for env in "${ENVIRONMENTS[@]}"; do
            echo -e "\n${YELLOW}$env Environment:${NC}"
            if [ -f "/tmp/agent_${env}_status.json" ]; then
                # Parse status file
                HOST_IP=$(grep -o '"host_ip": "[^"]*' "/tmp/agent_${env}_status.json" | cut -d'"' -f4)
                STATUS=$(grep -o '"status": "[^"]*' "/tmp/agent_${env}_status.json" | cut -d'"' -f4)
                STARTED=$(grep -o '"started_at": "[^"]*' "/tmp/agent_${env}_status.json" | cut -d'"' -f4)
                
                echo "  Status: $STATUS"
                echo "  Host IP: $HOST_IP"
                echo "  Started: $STARTED"
                
                # Check service health
                if curl -s "http://$HOST_IP:8000/health" > /dev/null 2>&1; then
                    echo -e "  Backend: ${GREEN}✅ Healthy${NC}"
                else
                    echo -e "  Backend: ${RED}❌ Not responding${NC}"
                fi
                
                if curl -s "http://$HOST_IP:3000" > /dev/null 2>&1; then
                    echo -e "  Frontend: ${GREEN}✅ Healthy${NC}"
                else
                    echo -e "  Frontend: ${RED}❌ Not responding${NC}"
                fi
            else
                echo -e "  Status: ${RED}❌ Not running${NC}"
            fi
        done
        ;;
    
    "health")
        echo -e "${BLUE}🏥 Health Check Report${NC}"
        for env in "${ENVIRONMENTS[@]}"; do
            if [ -f "/tmp/agent_${env}_status.json" ]; then
                HOST_IP=$(grep -o '"host_ip": "[^"]*' "/tmp/agent_${env}_status.json" | cut -d'"' -f4)
                echo -e "\n${YELLOW}Testing $env (${HOST_IP}):${NC}"
                
                # Test backend health endpoint
                if response=$(curl -s "http://$HOST_IP:8000/health" 2>/dev/null); then
                    echo -e "  Backend Health: ${GREEN}✅ OK${NC}"
                    echo "  Response: $response"
                else
                    echo -e "  Backend Health: ${RED}❌ Failed${NC}"
                fi
            fi
        done
        ;;
    
    "logs")
        ENV_NAME=${2:-"development"}
        echo -e "${BLUE}📝 Showing logs for $ENV_NAME environment${NC}"
        
        if [ -f "/tmp/backend_${ENV_NAME}_pid" ]; then
            echo -e "\n${YELLOW}Backend logs:${NC}"
            tail -n 50 "scripts/multi-env/logs/backend_${ENV_NAME}.log" 2>/dev/null || echo "No backend logs found"
        fi
        
        if [ -f "/tmp/frontend_${ENV_NAME}_pid" ]; then
            echo -e "\n${YELLOW}Frontend logs:${NC}"
            tail -n 50 "scripts/multi-env/logs/frontend_${ENV_NAME}.log" 2>/dev/null || echo "No frontend logs found"
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|health|logs [environment]}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all agent environments"
        echo "  stop    - Stop all agent environments"
        echo "  status  - Show status of all environments"
        echo "  health  - Run health checks on all environments"
        echo "  logs    - Show logs for specific environment"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs development"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Agent controller operation completed${NC}"
EOF

    chmod +x "scripts/multi-env/agent-controller.sh"
    echo -e "${GREEN}✅ Created master agent controller${NC}"
}

# Main deployment process
main() {
    echo -e "${BLUE}🚀 Starting agent deployment process...${NC}"
    
    # Create agents directory
    mkdir -p scripts/multi-env/agents
    mkdir -p scripts/multi-env/logs
    
    # Deploy agents to each environment
    echo -e "\n${BLUE}1. Deploying development agent${NC}"
    deploy_agent "development" "$DEV_IP" "latest"
    
    echo -e "\n${BLUE}2. Deploying staging agent${NC}"
    deploy_agent "staging" "$STAGING_IP" "stable"
    
    echo -e "\n${BLUE}3. Deploying production agent${NC}"
    deploy_agent "production" "$PROD_IP" "release"
    
    # Create master controller
    echo -e "\n${BLUE}4. Creating master agent controller${NC}"
    create_agent_controller
    
    # Create documentation
    cat > "scripts/multi-env/README.md" << 'EOF'
# ITDO_ERP2 Multi-Environment Agent Setup

This directory contains the multi-environment agent deployment system for ITDO_ERP2.

## Overview

The system creates three isolated environments:
- **Development** (172.23.14.204): Latest development code
- **Staging** (172.23.14.205): Stable testing environment  
- **Production** (172.23.14.206): Production-ready environment

## Quick Start

```bash
# Start all environments
./scripts/multi-env/agent-controller.sh start

# Check status
./scripts/multi-env/agent-controller.sh status

# Monitor environments
./scripts/multi-env/monitor-environments.sh

# Stop all environments
./scripts/multi-env/agent-controller.sh stop
```

## Environment URLs

| Environment | Backend API | Frontend | Database | Keycloak |
|-------------|-------------|----------|----------|----------|
| Development | http://172.23.14.204:8000 | http://172.23.14.204:3000 | 172.23.14.204:5432 | http://172.23.14.204:8080 |
| Staging     | http://172.23.14.205:8000 | http://172.23.14.205:3000 | 172.23.14.205:5432 | http://172.23.14.205:8080 |
| Production  | http://172.23.14.206:8000 | http://172.23.14.206:3000 | 172.23.14.206:5432 | http://172.23.14.206:8080 |

## File Structure

```
scripts/multi-env/
├── setup-multi-env.sh          # Initial setup script
├── agent-controller.sh          # Master controller
├── monitor-environments.sh      # Monitoring script
├── agents/
│   ├── development/
│   │   ├── agent-config.json    # Environment configuration
│   │   ├── start-agent.sh       # Start script
│   │   └── stop-agent.sh        # Stop script
│   ├── staging/
│   └── production/
└── environments/
    ├── development/
    │   ├── docker-compose.yml   # Data layer services
    │   └── .env                 # Environment variables
    ├── staging/
    └── production/
```

## Features

- **Isolated Environments**: Each environment has its own IP address and data
- **Automated Deployment**: One-command setup and deployment
- **Health Monitoring**: Continuous health checks and status reporting
- **Log Management**: Centralized logging for each environment
- **Configuration Management**: Environment-specific configurations

## Commands

### Agent Controller
```bash
./scripts/multi-env/agent-controller.sh start     # Start all environments
./scripts/multi-env/agent-controller.sh stop      # Stop all environments
./scripts/multi-env/agent-controller.sh status    # Show status
./scripts/multi-env/agent-controller.sh health    # Health checks
./scripts/multi-env/agent-controller.sh logs dev  # Show logs
```

### Individual Environment
```bash
./scripts/multi-env/agents/development/start-agent.sh
./scripts/multi-env/agents/development/stop-agent.sh
```

### Monitoring
```bash
./scripts/multi-env/monitor-environments.sh       # Full status report
```

## Troubleshooting

### IP Address Issues
```bash
# Check configured IPs
ip addr show eth0

# Manually add IP (if needed)
sudo ip addr add 172.23.14.204/20 dev eth0
```

### Service Issues
```bash
# Check service status
./scripts/multi-env/agent-controller.sh status

# Check specific service health
curl http://172.23.14.204:8000/health
```

### Resource Usage
```bash
# Check system resources
free -h
df -h
ps aux | grep -E "(uvicorn|npm|node)"
```

## Implementation Details

This setup implements Issue #147 requirements:
- Multiple verification environments on single PC
- Port conflict resolution using IP address separation
- Automated agent deployment and management
- Resource monitoring and optimization
- Environment isolation with separate databases

EOF

    echo -e "\n${GREEN}🎉 Agent Deployment Setup Complete!${NC}"
    echo "===================================="
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Start all environments: ./scripts/multi-env/agent-controller.sh start"
    echo "2. Check status: ./scripts/multi-env/agent-controller.sh status"
    echo "3. Monitor health: ./scripts/multi-env/monitor-environments.sh"
    echo ""
    echo -e "${BLUE}Environment Access:${NC}"
    echo "  Development: http://${DEV_IP}:8000"
    echo "  Staging:     http://${STAGING_IP}:8000"
    echo "  Production:  http://${PROD_IP}:8000"
}

# Run main function
main "$@"