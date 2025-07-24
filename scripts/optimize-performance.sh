#!/bin/bash
set -euo pipefail

echo "=== Performance Optimization Script ==="

# 1. Database indexing
echo "Creating database indexes..."
psql $DATABASE_URL << SQL
-- User table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_is_active ON users(is_active) WHERE is_active = true;

-- Audit log indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at DESC);

-- Session indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

ANALYZE;
SQL

# 2. Redis optimization
echo "Optimizing Redis..."
redis-cli --pass $REDIS_PASSWORD << REDIS
CONFIG SET maxmemory-policy allkeys-lru
CONFIG SET maxmemory 512mb
CONFIG SET save ""
CONFIG REWRITE
REDIS

# 3. Application profiling
echo "Running application profiling..."
cd backend
uv run python -m cProfile -o profile.stats app/main.py &
APP_PID=$!
sleep 30
kill $APP_PID

# Analyze profile
uv run python << PYTHON
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
print("\n=== Top 20 Time Consuming Functions ===")
p.print_stats(20)
PYTHON

# 4. Frontend bundle analysis
echo "Analyzing frontend bundle..."
cd ../frontend
npm run build -- --analyze