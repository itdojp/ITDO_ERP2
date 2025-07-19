#!/bin/bash
# Monitor all environments

echo "=== Multi-Environment Status ==="
echo "$(date)"
echo

# Check container status
echo "Container Status:"
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

# Check network interfaces
echo "Network Interfaces:"
ip addr show eth0 | grep inet
echo

# Check port usage
echo "Port Usage:"
ss -tuln | grep -E ":(8000|8001|8002|3000|3001|3002|5432|5433|5434|6379|6380|6381) "
echo

# Check system resources
echo "System Resources:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"
