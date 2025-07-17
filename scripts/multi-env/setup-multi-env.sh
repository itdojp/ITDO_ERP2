#!/bin/bash

# Multi-Environment Agent Setup Script for ITDO_ERP2
# Implements Issue #147: Multiple verification environments

set -e

# Configuration
BASE_IP="172.23.14"
SUBNET="/20"
DEV_IP="${BASE_IP}.204"
STAGING_IP="${BASE_IP}.205" 
PROD_IP="${BASE_IP}.206"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 ITDO_ERP2 Multi-Environment Setup${NC}"
echo "======================================"

# Function to check if IP exists
check_ip_exists() {
    local ip=$1
    ip addr show dev eth0 | grep -q "${ip}${SUBNET}"
}

# Function to add IP address
add_ip_address() {
    local ip=$1
    local env_name=$2
    
    if check_ip_exists "$ip"; then
        echo -e "${YELLOW}⚠️  IP $ip already exists for $env_name environment${NC}"
    else
        echo -e "${BLUE}➕ Adding IP $ip for $env_name environment${NC}"
        sudo ip addr add "${ip}${SUBNET}" dev eth0
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully added IP $ip${NC}"
        else
            echo -e "${RED}❌ Failed to add IP $ip${NC}"
            exit 1
        fi
    fi
}

# Function to create environment directory
create_env_directory() {
    local env_name=$1
    local env_dir="environments/${env_name}"
    
    echo -e "${BLUE}📁 Creating directory structure for ${env_name}${NC}"
    mkdir -p "$env_dir"/{config,data,logs}
    
    # Create environment-specific compose file
    cat > "$env_dir/docker-compose.yml" << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: ${env_name}-postgres
    environment:
      POSTGRES_DB: itdo_erp_${env_name}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - ${env_name}_postgres_data:/var/lib/postgresql/data
    networks:
      - ${env_name}_network

  redis:
    image: redis:7-alpine
    container_name: ${env_name}-redis
    volumes:
      - ${env_name}_redis_data:/data
    networks:
      - ${env_name}_network

  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    container_name: ${env_name}-keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://${env_name}-postgres:5432/itdo_erp_${env_name}
      KC_DB_USERNAME: postgres
      KC_DB_PASSWORD: postgres
    command: start-dev
    depends_on:
      - postgres
    networks:
      - ${env_name}_network

  pgadmin:
    image: dpage/pgadmin4:8
    container_name: ${env_name}-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@itdo.local
      PGADMIN_DEFAULT_PASSWORD: admin
    volumes:
      - ${env_name}_pgadmin_data:/var/lib/pgadmin
    networks:
      - ${env_name}_network

networks:
  ${env_name}_network:
    driver: bridge

volumes:
  ${env_name}_postgres_data:
  ${env_name}_redis_data:
  ${env_name}_pgadmin_data:
EOF

    # Create environment-specific configuration
    cat > "$env_dir/.env" << EOF
# Environment: ${env_name}
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/itdo_erp_${env_name}
REDIS_URL=redis://localhost:6379/0
KEYCLOAK_URL=http://localhost:8080
ENVIRONMENT=${env_name}

# Service URLs for this environment
BACKEND_URL=http://${2}:8000
FRONTEND_URL=http://${2}:3000
DATABASE_PORT=5432
REDIS_PORT=6379
KEYCLOAK_PORT=8080
PGADMIN_PORT=8081
EOF

    echo -e "${GREEN}✅ Created environment directory: $env_dir${NC}"
}

# Function to create startup script for environment
create_startup_script() {
    local env_name=$1
    local ip=$2
    
    cat > "scripts/multi-env/start-${env_name}.sh" << EOF
#!/bin/bash

# Start ${env_name} environment
echo "🚀 Starting ${env_name} environment on IP ${ip}"

# Ensure IP is configured
if ! ip addr show dev eth0 | grep -q "${ip}${SUBNET}"; then
    echo "Adding IP ${ip} for ${env_name} environment"
    sudo ip addr add "${ip}${SUBNET}" dev eth0
fi

# Start data layer services
cd environments/${env_name}
podman-compose up -d

# Bind services to specific IP
echo "⚙️  Configuring services for IP ${ip}"

# PostgreSQL
podman exec ${env_name}-postgres sh -c "
    if ! grep -q 'listen_addresses' /var/lib/postgresql/data/postgresql.conf; then
        echo \"listen_addresses = '${ip}'\" >> /var/lib/postgresql/data/postgresql.conf
    fi
"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Service Status:"
podman ps --filter "name=${env_name}-"

echo "🌐 ${env_name} Environment URLs:"
echo "  Backend API: http://${ip}:8000"
echo "  Frontend: http://${ip}:3000"
echo "  PostgreSQL: ${ip}:5432"
echo "  Redis: ${ip}:6379"
echo "  Keycloak: http://${ip}:8080"
echo "  pgAdmin: http://${ip}:8081"

echo "✅ ${env_name} environment started successfully"
EOF

    chmod +x "scripts/multi-env/start-${env_name}.sh"
    echo -e "${GREEN}✅ Created startup script: start-${env_name}.sh${NC}"
}

# Function to create monitoring script
create_monitoring_script() {
    cat > "scripts/multi-env/monitor-environments.sh" << EOF
#!/bin/bash

# Multi-Environment Monitoring Script
echo "📊 ITDO_ERP2 Multi-Environment Status"
echo "===================================="

check_env_status() {
    local env_name=\$1
    local ip=\$2
    
    echo ""
    echo "🔍 Environment: \$env_name (IP: \$ip)"
    echo "------------------------------------"
    
    # Check IP configuration
    if ip addr show dev eth0 | grep -q "\${ip}${SUBNET}"; then
        echo "✅ IP \$ip is configured"
    else
        echo "❌ IP \$ip is NOT configured"
    fi
    
    # Check container status
    echo "Container Status:"
    podman ps --filter "name=\$env_name-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Check service connectivity
    if curl -s "http://\$ip:8000/health" > /dev/null 2>&1; then
        echo "✅ Backend API is responsive"
    else
        echo "❌ Backend API is not responsive"
    fi
}

# Check all environments
check_env_status "development" "${DEV_IP}"
check_env_status "staging" "${STAGING_IP}"
check_env_status "production" "${PROD_IP}"

echo ""
echo "📈 Resource Usage:"
echo "Memory: \$(free -h | grep 'Mem:' | awk '{print \$3 \"/\" \$2}')"
echo "Disk: \$(df -h / | tail -1 | awk '{print \$3 \"/\" \$2 \" (\" \$5 \" used)\"}')"

echo ""
echo "🔗 Quick Access URLs:"
echo "Development:  http://${DEV_IP}:8000"
echo "Staging:      http://${STAGING_IP}:8000" 
echo "Production:   http://${PROD_IP}:8000"
EOF

    chmod +x "scripts/multi-env/monitor-environments.sh"
    echo -e "${GREEN}✅ Created monitoring script${NC}"
}

# Main setup process
main() {
    echo -e "${BLUE}🚀 Starting multi-environment setup...${NC}"
    
    # Create base directories
    mkdir -p scripts/multi-env/environments/{development,staging,production}
    mkdir -p scripts/multi-env/logs
    
    # Add IP addresses
    echo -e "\n${BLUE}1. Configuring IP addresses${NC}"
    add_ip_address "$DEV_IP" "development"
    add_ip_address "$STAGING_IP" "staging"
    add_ip_address "$PROD_IP" "production"
    
    # Create environment directories and configs
    echo -e "\n${BLUE}2. Creating environment configurations${NC}"
    create_env_directory "development" "$DEV_IP"
    create_env_directory "staging" "$STAGING_IP"
    create_env_directory "production" "$PROD_IP"
    
    # Create startup scripts
    echo -e "\n${BLUE}3. Creating startup scripts${NC}"
    create_startup_script "development" "$DEV_IP"
    create_startup_script "staging" "$STAGING_IP"
    create_startup_script "production" "$PROD_IP"
    
    # Create monitoring script
    echo -e "\n${BLUE}4. Creating monitoring tools${NC}"
    create_monitoring_script
    
    # Create auto-setup for bashrc
    echo -e "\n${BLUE}5. Setting up automatic IP configuration${NC}"
    
    # Check if already in bashrc
    if ! grep -q "ITDO_ERP2 Multi-Environment IPs" ~/.bashrc; then
        cat >> ~/.bashrc << EOF

# ITDO_ERP2 Multi-Environment IPs
if ! ip addr show dev eth0 | grep -q "${DEV_IP}${SUBNET}"; then
    sudo ip addr add "${DEV_IP}${SUBNET}" dev eth0 2>/dev/null || true
fi
if ! ip addr show dev eth0 | grep -q "${STAGING_IP}${SUBNET}"; then
    sudo ip addr add "${STAGING_IP}${SUBNET}" dev eth0 2>/dev/null || true
fi
if ! ip addr show dev eth0 | grep -q "${PROD_IP}${SUBNET}"; then
    sudo ip addr add "${PROD_IP}${SUBNET}" dev eth0 2>/dev/null || true
fi
EOF
        echo -e "${GREEN}✅ Added automatic IP setup to ~/.bashrc${NC}"
    else
        echo -e "${YELLOW}⚠️  Automatic IP setup already exists in ~/.bashrc${NC}"
    fi
    
    # Display final status
    echo -e "\n${GREEN}🎉 Multi-Environment Setup Complete!${NC}"
    echo "======================================"
    echo -e "${BLUE}Available Environments:${NC}"
    echo "  🔧 Development:  ${DEV_IP}:8000"
    echo "  🧪 Staging:      ${STAGING_IP}:8000"
    echo "  🚀 Production:   ${PROD_IP}:8000"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  Start environment: ./scripts/multi-env/start-development.sh"
    echo "  Monitor all:       ./scripts/multi-env/monitor-environments.sh"
    echo "  Check IPs:         ip addr show eth0"
    echo ""
    echo -e "${YELLOW}Note: Restart your terminal to activate automatic IP configuration${NC}"
}

# Run main function
main "$@"