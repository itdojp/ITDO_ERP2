#!/bin/bash

# Start development environment
echo "🚀 Starting development environment on IP 172.23.14.204"

# Ensure IP is configured
if ! ip addr show dev eth0 | grep -q "172.23.14.204/20"; then
    echo "Adding IP 172.23.14.204 for development environment"
    sudo ip addr add "172.23.14.204/20" dev eth0
fi

# Start data layer services
cd environments/development
podman-compose up -d

# Bind services to specific IP
echo "⚙️  Configuring services for IP 172.23.14.204"

# PostgreSQL
podman exec development-postgres sh -c "
    if ! grep -q 'listen_addresses' /var/lib/postgresql/data/postgresql.conf; then
        echo \"listen_addresses = '172.23.14.204'\" >> /var/lib/postgresql/data/postgresql.conf
    fi
"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Service Status:"
podman ps --filter "name=development-"

echo "🌐 development Environment URLs:"
echo "  Backend API: http://172.23.14.204:8000"
echo "  Frontend: http://172.23.14.204:3000"
echo "  PostgreSQL: 172.23.14.204:5432"
echo "  Redis: 172.23.14.204:6379"
echo "  Keycloak: http://172.23.14.204:8080"
echo "  pgAdmin: http://172.23.14.204:8081"

echo "✅ development environment started successfully"
