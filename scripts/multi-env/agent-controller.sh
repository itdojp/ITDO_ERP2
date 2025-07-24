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
