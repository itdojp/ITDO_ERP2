#!/bin/bash
# Start dev environment containers

set -e

ENV_NAME="dev"
IP_ADDR="172.20.10.2"
CONFIG_DIR="/home/work/ITDO_ERP2/configs/dev"

echo "Starting $ENV_NAME environment..."

# Check if ports are available
if ss -tuln | grep -q ":5435 "; then
    echo "Port 5435 is already in use"
    exit 1
fi

if ss -tuln | grep -q ":6382 "; then
    echo "Port 6382 is already in use"
    exit 1
fi

# Create data directories
mkdir -p "$CONFIG_DIR/postgres-data"
mkdir -p "$CONFIG_DIR/redis-data"

# Start PostgreSQL
echo "Starting PostgreSQL for $ENV_NAME..."
podman run -d \
    --name "itdo-postgres-$ENV_NAME" \
    --network host \
    -e POSTGRES_DB="itdo_erp_dev" \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -v "$CONFIG_DIR/postgres-data:/var/lib/postgresql/data" \
    -p 172.20.10.2:5435:5432 \
    postgres:15-alpine

# Start Redis
echo "Starting Redis for $ENV_NAME..."
podman run -d \
    --name "itdo-redis-$ENV_NAME" \
    --network host \
    -p 172.20.10.2:6382:6379 \
    redis:7-alpine redis-server --appendonly yes

# Wait for services to be ready
sleep 10

echo "$ENV_NAME environment started successfully!"
echo "PostgreSQL: 172.20.10.2:5435"
echo "Redis: 172.20.10.2:6382"
echo "Backend will be available at: http://172.20.10.2:8000"
echo "Frontend will be available at: http://172.20.10.2:3000"
