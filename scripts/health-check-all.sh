#!/bin/bash
echo "=== System Health Check ==="
echo -n "PostgreSQL: "
pg_isready -h localhost -p 5432 && echo "✓" || echo "✗"

echo -n "Redis: "
redis-cli ping >/dev/null 2>&1 && echo "✓" || echo "✗"

echo -n "Backend API: "
curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "✓" || echo "✗"

echo -n "Frontend: "
curl -s http://localhost:3000 >/dev/null 2>&1 && echo "✓" || echo "✗"

echo -n "Keycloak: "
curl -s http://localhost:8080 >/dev/null 2>&1 && echo "✓" || echo "✗"

echo -n "pgAdmin: "
curl -s http://localhost:8081 >/dev/null 2>&1 && echo "✓" || echo "✗"