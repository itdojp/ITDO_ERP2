#!/bin/bash
# ITDO ERP v2 - Clean SSL Certificate Setup
# CC03 v60.0 - Clean Production Implementation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    local ssl_dir="../nginx/ssl"
    mkdir -p "$ssl_dir"
    
    if [[ ! -f "$ssl_dir/cert.pem" ]] || [[ ! -f "$ssl_dir/key.pem" ]]; then
        log "Generating self-signed SSL certificate for development..."
        
        # Generate private key
        openssl genrsa -out "$ssl_dir/key.pem" 2048
        
        # Generate certificate
        openssl req -new -x509 -key "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 \
            -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO/CN=itdo-erp.com" \
            -addext "subjectAltName=DNS:itdo-erp.com,DNS:www.itdo-erp.com,DNS:api.itdo-erp.com,DNS:auth.itdo-erp.com,DNS:monitoring.itdo-erp.com"
        
        # Set proper permissions
        chmod 600 "$ssl_dir/key.pem"
        chmod 644 "$ssl_dir/cert.pem"
        
        log "SSL certificates generated successfully"
        warn "Please replace self-signed certificates with production certificates"
    else
        log "SSL certificates already exist"
    fi
}

# Generate secure passwords
generate_secure_passwords() {
    log "Generating secure passwords..."
    
    local env_file="../compose/.env.production.secure"
    
    if [[ ! -f "$env_file" ]]; then
        cp "../compose/.env.production" "$env_file"
        
        # Generate secure passwords
        local secret_key=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
        local jwt_secret=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
        local postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        local redis_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        local keycloak_admin_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        local keycloak_client_secret=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        local grafana_admin_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        
        # Replace placeholders
        sed -i "s/your-secret-key-change-in-production/$secret_key/" "$env_file"
        sed -i "s/your-jwt-secret-change-in-production/$jwt_secret/" "$env_file"
        sed -i "s/your-postgres-password-change-in-production/$postgres_password/" "$env_file"
        sed -i "s/your-redis-password-change-in-production/$redis_password/" "$env_file"
        sed -i "s/your-keycloak-admin-password-change-in-production/$keycloak_admin_password/" "$env_file"
        sed -i "s/your-keycloak-client-secret-change-in-production/$keycloak_client_secret/" "$env_file"
        sed -i "s/your-grafana-admin-password-change-in-production/$grafana_admin_password/" "$env_file"
        
        # Update Redis config with password
        sed -i "s/your-redis-password-change-in-production/$redis_password/" redis.conf
        
        # Set restrictive permissions
        chmod 600 "$env_file"
        
        log "Secure environment file created: $env_file"
        warn "Please review and update the configuration as needed"
    else
        log "Secure environment file already exists"
    fi
}

# Main function
main() {
    log "Starting SSL and security setup..."
    
    setup_ssl
    generate_secure_passwords
    
    log "SSL and security setup completed successfully!"
    warn "Important next steps:"
    warn "1. Replace self-signed certificates with production certificates"
    warn "2. Review the generated secure environment file"
    warn "3. Configure DNS records for your domains"
    warn "4. Update monitoring and alerting endpoints"
}

# Check if running in correct directory
if [[ ! -f "setup-ssl.sh" ]]; then
    error "Please run this script from the infra-clean/security directory"
    exit 1
fi

main "$@"