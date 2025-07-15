#!/bin/bash
# Start prod environment containers

set -e

ENV_NAME="prod"
IP_ADDR="172.20.10.4"
CONFIG_DIR="/home/work/ITDO_ERP2/configs/prod"

echo "Starting $ENV_NAME environment..."

# Check if ports are available
if ss -tuln | grep -q ":5434 "; then
    echo "Port 5434 is already in use"
    exit 1
fi

if ss -tuln | grep -q ":6381 "; then
    echo "Port 6381 is already in use"
    exit 1
fi

# Start PostgreSQL
echo "Starting PostgreSQL for $ENV_NAME..."
podman run -d \
    --name "itdo-postgres-$ENV_NAME" \
    --network host \
    -e POSTGRES_DB="itdo_erp_prod" \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -v "$CONFIG_DIR/postgres-data:/var/lib/postgresql/data" \
    -p 172.20.10.4:5434:5432 \
    postgres:15-alpine

# Start Redis
echo "Starting Redis for $ENV_NAME..."
podman run -d \
    --name "itdo-redis-$ENV_NAME" \
    --network host \
    -p 172.20.10.4:6381:6379 \
    redis:7-alpine redis-server --appendonly yes

# Wait for services to be ready
sleep 10

echo "$ENV_NAME environment started successfully!"
echo "PostgreSQL: 172.20.10.4:5434"
echo "Redis: 172.20.10.4:6381"
echo "Backend will be available at: http://172.20.10.4:8002"
echo "Frontend will be available at: http://172.20.10.4:3002"
