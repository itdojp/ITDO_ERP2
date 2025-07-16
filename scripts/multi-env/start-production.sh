#!/bin/bash

# Start production environment
echo "🚀 Starting production environment on IP 172.23.14.206"

# Ensure IP is configured
if ! ip addr show dev eth0 | grep -q "172.23.14.206/20"; then
    echo "Adding IP 172.23.14.206 for production environment"
    sudo ip addr add "172.23.14.206/20" dev eth0
fi

# Start data layer services
cd environments/production
podman-compose up -d

# Bind services to specific IP
echo "⚙️  Configuring services for IP 172.23.14.206"

# PostgreSQL
podman exec production-postgres sh -c "
    if ! grep -q 'listen_addresses' /var/lib/postgresql/data/postgresql.conf; then
        echo \"listen_addresses = '172.23.14.206'\" >> /var/lib/postgresql/data/postgresql.conf
    fi
"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Service Status:"
podman ps --filter "name=production-"

echo "🌐 production Environment URLs:"
echo "  Backend API: http://172.23.14.206:8000"
echo "  Frontend: http://172.23.14.206:3000"
echo "  PostgreSQL: 172.23.14.206:5432"
echo "  Redis: 172.23.14.206:6379"
echo "  Keycloak: http://172.23.14.206:8080"
echo "  pgAdmin: http://172.23.14.206:8081"

echo "✅ production environment started successfully"
