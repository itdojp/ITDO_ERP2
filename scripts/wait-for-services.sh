#!/bin/bash
set -e

echo "Waiting for services to be ready..."

# Function to wait for a service
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=${4:-60}
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port > /dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Function to wait for HTTP service
wait_for_http() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-60}
    local attempt=1

    echo "Waiting for $service_name at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s $url > /dev/null 2>&1; then
            echo "$service_name HTTP endpoint is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service_name HTTP not ready, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: $service_name HTTP endpoint failed to become ready after $max_attempts attempts"
    return 1
}

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "localhost" "5432"

# Wait for Redis
wait_for_service "Redis" "localhost" "6379"

# Test database connectivity
echo "Testing PostgreSQL connection..."
if command -v psql > /dev/null 2>&1; then
    PGPASSWORD=itdo_password psql -h localhost -U itdo_user -d itdo_erp_test -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "PostgreSQL connection test successful!"
    else
        echo "ERROR: PostgreSQL connection test failed!"
        exit 1
    fi
else
    echo "psql not available, skipping connection test"
fi

# Test Redis connectivity
echo "Testing Redis connection..."
if command -v redis-cli > /dev/null 2>&1; then
    redis-cli -h localhost ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Redis connection test successful!"
    else
        echo "ERROR: Redis connection test failed!"
        exit 1
    fi
else
    echo "redis-cli not available, skipping connection test"
fi

# Wait for backend service (if running)
if [ "$1" = "--include-backend" ]; then
    wait_for_http "Backend API" "http://localhost:8000/health"
fi

echo "All services are ready!"