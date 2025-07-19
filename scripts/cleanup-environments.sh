#!/bin/bash
# Cleanup all environments

echo "Cleaning up all environments..."

# Stop and remove containers
for env in dev staging prod; do
    echo "Cleaning up $env environment..."
    podman stop "itdo-postgres-$env" 2>/dev/null || true
    podman stop "itdo-redis-$env" 2>/dev/null || true
    podman rm "itdo-postgres-$env" 2>/dev/null || true
    podman rm "itdo-redis-$env" 2>/dev/null || true
done

# Remove additional IP addresses (would need sudo in real environment)
echo "# sudo ip addr del 172.20.10.2/20 dev eth0" 
echo "# sudo ip addr del 172.20.10.3/20 dev eth0"
echo "# sudo ip addr del 172.20.10.4/20 dev eth0"

echo "Cleanup completed"
