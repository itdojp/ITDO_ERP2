#!/bin/bash

# Multi-Environment Monitoring Script
echo "📊 ITDO_ERP2 Multi-Environment Status"
echo "===================================="

check_env_status() {
    local env_name=$1
    local ip=$2
    
    echo ""
    echo "🔍 Environment: $env_name (IP: $ip)"
    echo "------------------------------------"
    
    # Check IP configuration
    if ip addr show dev eth0 | grep -q "${ip}/20"; then
        echo "✅ IP $ip is configured"
    else
        echo "❌ IP $ip is NOT configured"
    fi
    
    # Check container status
    echo "Container Status:"
    podman ps --filter "name=$env_name-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Check service connectivity
    if curl -s "http://$ip:8000/health" > /dev/null 2>&1; then
        echo "✅ Backend API is responsive"
    else
        echo "❌ Backend API is not responsive"
    fi
}

# Check all environments
check_env_status "development" "172.23.14.204"
check_env_status "staging" "172.23.14.205"
check_env_status "production" "172.23.14.206"

echo ""
echo "📈 Resource Usage:"
echo "Memory: $(free -h | grep 'Mem:' | awk '{print $3 \"/\" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 \"/\" $2 \" (\" $5 \" used)\"}')"

echo ""
echo "🔗 Quick Access URLs:"
echo "Development:  http://172.23.14.204:8000"
echo "Staging:      http://172.23.14.205:8000" 
echo "Production:   http://172.23.14.206:8000"
