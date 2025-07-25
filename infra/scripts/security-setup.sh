#!/bin/bash
# ITDO ERP v2 - Production Security Setup Script
# CC03 v59.0 - Practical Production Infrastructure

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Generate secure passwords
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    local ssl_dir="$(dirname "$0")/../nginx/ssl"
    mkdir -p "$ssl_dir"
    
    if [[ ! -f "$ssl_dir/cert.pem" ]] || [[ ! -f "$ssl_dir/key.pem" ]]; then
        log "Generating self-signed SSL certificate for development..."
        
        # Generate private key
        openssl genrsa -out "$ssl_dir/key.pem" 2048
        
        # Generate certificate
        openssl req -new -x509 -key "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO/CN=itdo-erp.com"
        
        # Set proper permissions
        chmod 600 "$ssl_dir/key.pem"
        chmod 644 "$ssl_dir/cert.pem"
        
        log "SSL certificates generated"
    else
        log "SSL certificates already exist"
    fi
}

# Generate secure environment file
setup_environment() {
    log "Setting up secure environment configuration..."
    
    local env_file="$(dirname "$0")/../.env.production"
    local env_secure_file="$(dirname "$0")/../.env.production.secure"
    
    if [[ ! -f "$env_secure_file" ]]; then
        log "Generating secure environment file..."
        
        # Copy template
        cp "$env_file" "$env_secure_file"
        
        # Generate secure passwords
        local secret_key=$(generate_password 64)
        local jwt_secret=$(generate_password 64)
        local postgres_password=$(generate_password 32)
        local redis_password=$(generate_password 32)
        local keycloak_admin_password=$(generate_password 32)
        local keycloak_db_password=$(generate_password 32)
        local grafana_admin_password=$(generate_password 32)
        
        # Replace placeholders with secure values
        sed -i "s/your-super-secret-key-change-in-production/$secret_key/" "$env_secure_file"
        sed -i "s/your-jwt-secret-key-change-in-production/$jwt_secret/" "$env_secure_file"
        sed -i "s/your-postgres-password-change-in-production/$postgres_password/" "$env_secure_file"
        sed -i "s/your-redis-password-change-in-production/$redis_password/" "$env_secure_file"
        sed -i "s/your-keycloak-admin-password-change-in-production/$keycloak_admin_password/" "$env_secure_file"
        sed -i "s/your-keycloak-db-password-change-in-production/$keycloak_db_password/" "$env_secure_file"
        sed -i "s/your-grafana-admin-password-change-in-production/$grafana_admin_password/" "$env_secure_file"
        
        # Set restrictive permissions
        chmod 600 "$env_secure_file"
        
        log "Secure environment file created: $env_secure_file"
        warn "Please review and update the configuration as needed"
    else
        log "Secure environment file already exists"
    fi
}

# Setup database security
setup_database_security() {
    log "Setting up database security configuration..."
    
    local postgres_dir="$(dirname "$0")/../postgres"
    mkdir -p "$postgres_dir"
    
    # PostgreSQL configuration for security
    cat > "$postgres_dir/postgresql.conf" << 'EOF'
# PostgreSQL Security Configuration
# CC03 v59.0 - Practical Production Infrastructure

# Connection Settings
listen_addresses = '*'
port = 5432
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Security Settings
ssl = on
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
password_encryption = scram-sha-256

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_lock_waits = on
log_statement = 'ddl'
log_temp_files = 10MB

# Resource Usage
shared_preload_libraries = 'pg_stat_statements'
track_activity_query_size = 1024
track_counts = on
track_functions = pl

# Checkpoints
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
EOF

    # PostgreSQL host-based authentication
    cat > "$postgres_dir/pg_hba.conf" << 'EOF'
# PostgreSQL Host-Based Authentication
# CC03 v59.0 - Practical Production Infrastructure

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             all                                     peer

# Docker network connections
host    all             all             172.16.0.0/12           scram-sha-256
host    all             all             192.168.0.0/16          scram-sha-256
host    all             all             10.0.0.0/8              scram-sha-256

# Deny all other connections
host    all             all             0.0.0.0/0               reject
EOF

    log "Database security configuration created"
}

# Setup Redis security
setup_redis_security() {
    log "Setting up Redis security configuration..."
    
    local redis_dir="$(dirname "$0")/../redis"
    mkdir -p "$redis_dir"
    
    cat > "$redis_dir/redis.conf" << 'EOF'
# Redis Security Configuration
# CC03 v59.0 - Practical Production Infrastructure

# Network Security
bind 0.0.0.0
protected-mode yes
port 6379

# Authentication
requirepass REDIS_PASSWORD_PLACEHOLDER

# General Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
rename-command EVAL ""
rename-command DEBUG ""
rename-command SHUTDOWN SHUTDOWN_CMD

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# Append Only File
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Logging
loglevel notice
logfile ""

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# TCP Settings
tcp-keepalive 300
timeout 0
tcp-backlog 511
EOF

    log "Redis security configuration created"
}

# Setup firewall rules
setup_firewall() {
    log "Setting up firewall rules..."
    
    if command -v ufw &> /dev/null; then
        # Enable UFW
        sudo ufw --force enable
        
        # Default policies
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        
        # Allow SSH
        sudo ufw allow 22/tcp
        
        # Allow HTTP/HTTPS
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        # Allow monitoring ports (restrict to internal networks)
        sudo ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
        sudo ufw allow from 10.0.0.0/8 to any port 3001  # Grafana
        sudo ufw allow from 10.0.0.0/8 to any port 9093  # Alertmanager
        
        # Deny dangerous ports
        sudo ufw deny 5432/tcp  # PostgreSQL (should only be accessible via Docker network)
        sudo ufw deny 6379/tcp  # Redis (should only be accessible via Docker network)
        
        log "Firewall rules configured"
    else
        warn "UFW not available, please configure firewall manually"
    fi
}

# Setup fail2ban
setup_fail2ban() {
    log "Setting up fail2ban..."
    
    if command -v fail2ban-client &> /dev/null; then
        # Configure fail2ban jail
        sudo tee /etc/fail2ban/jail.local << 'EOF' > /dev/null
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
        
        # Restart fail2ban
        sudo systemctl restart fail2ban
        sudo systemctl enable fail2ban
        
        log "Fail2ban configured"
    else
        warn "Fail2ban not installed, please install and configure manually"
    fi
}

# Setup security monitoring
setup_security_monitoring() {
    log "Setting up security monitoring..."
    
    local monitoring_dir="$(dirname "$0")/../monitoring"
    
    # Create security-specific alert rules
    cat >> "$monitoring_dir/alert-rules.yml" << 'EOF'

  # Security alerts
  - name: security-alerts
    rules:
      - alert: TooManyFailedLogins
        expr: increase(nginx_http_requests_total{status="401"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Too many failed login attempts"
          description: "More than 10 failed login attempts in 5 minutes"

      - alert: SuspiciousTraffic
        expr: increase(nginx_http_requests_total{status="404"}[5m]) > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Suspicious traffic detected"
          description: "High number of 404 errors may indicate scanning attempts"

      - alert: UnauthorizedAccess
        expr: increase(nginx_http_requests_total{status="403"}[5m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Unauthorized access attempts"
          description: "Multiple 403 Forbidden responses detected"
EOF

    log "Security monitoring configured"
}

# Generate security report
generate_security_report() {
    log "Generating security report..."
    
    local report_file="/tmp/security-setup-report.txt"
    
    cat > "$report_file" << EOF
ITDO ERP v2 - Security Setup Report
Generated: $(date)

SSL Certificates:
- Location: $(dirname "$0")/../nginx/ssl/
- Certificate: $([ -f "$(dirname "$0")/../nginx/ssl/cert.pem" ] && echo "✓ Present" || echo "✗ Missing")
- Private Key: $([ -f "$(dirname "$0")/../nginx/ssl/key.pem" ] && echo "✓ Present" || echo "✗ Missing")

Environment Security:
- Secure env file: $([ -f "$(dirname "$0")/../.env.production.secure" ] && echo "✓ Created" || echo "✗ Missing")

Database Security:
- PostgreSQL config: $([ -f "$(dirname "$0")/../postgres/postgresql.conf" ] && echo "✓ Configured" || echo "✗ Missing")
- HBA config: $([ -f "$(dirname "$0")/../postgres/pg_hba.conf" ] && echo "✓ Configured" || echo "✗ Missing")

Redis Security:
- Redis config: $([ -f "$(dirname "$0")/../redis/redis.conf" ] && echo "✓ Configured" || echo "✗ Missing")

System Security:
- UFW status: $(sudo ufw status | grep "Status:" | cut -d' ' -f2 || echo "Unknown")
- Fail2ban: $(systemctl is-active fail2ban 2>/dev/null || echo "Not running")

Security Monitoring:
- Alert rules: $([ -f "$(dirname "$0")/../monitoring/alert-rules.yml" ] && echo "✓ Configured" || echo "✗ Missing")

Recommendations:
1. Review and update all generated passwords
2. Configure proper SSL certificates for production
3. Set up log rotation and monitoring
4. Configure backup encryption
5. Review firewall rules for your environment
6. Set up intrusion detection system
7. Configure security scanning tools
8. Implement security headers validation
9. Set up vulnerability scanning
10. Configure security incident response procedures

EOF

    log "Security report generated: $report_file"
    cat "$report_file"
}

# Main security setup function
main() {
    log "Starting ITDO ERP v2 security setup..."
    
    setup_ssl
    setup_environment
    setup_database_security
    setup_redis_security
    setup_firewall
    setup_fail2ban
    setup_security_monitoring
    generate_security_report
    
    log "Security setup completed successfully!"
    warn "Please review the generated configurations and update them according to your security requirements"
    warn "Remember to:"
    warn "1. Use the .env.production.secure file instead of .env.production"
    warn "2. Replace self-signed certificates with proper SSL certificates"
    warn "3. Review and adjust firewall rules for your environment" 
    warn "4. Configure monitoring and alerting endpoints"
}

# Check if running as root for certain operations
check_privileges() {
    if [[ $EUID -ne 0 ]] && [[ "${1:-}" != "--no-root" ]]; then
        warn "Some security setup operations require root privileges"
        warn "Run with --no-root to skip system-level configuration"
        read -p "Continue with limited setup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --no-root    Skip system-level security configuration"
    echo "  --help       Show this help message"
}

# Parse arguments
case "${1:-}" in
    "--help"|"-h")
        usage
        exit 0
        ;;
    "--no-root")
        log "Running security setup without system-level configuration"
        main
        ;;
    "")
        check_privileges
        main
        ;;
    *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
esac