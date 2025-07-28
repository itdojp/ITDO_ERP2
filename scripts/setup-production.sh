#!/bin/bash
#
# ITDO ERP v2 - Production Setup Script
# This script helps set up the production environment
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_USER="itdo-erp"
APP_DIR="/home/${APP_USER}/ITDO_ERP2"
DOMAIN=""
DB_NAME="itdo_erp_prod"
DB_USER="itdo_erp"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

get_input() {
    local prompt="$1"
    local var_name="$2"
    local default="${3:-}"
    
    if [[ -n "$default" ]]; then
        read -p "$prompt [$default]: " value
        value="${value:-$default}"
    else
        read -p "$prompt: " value
    fi
    
    eval "$var_name='$value'"
}

generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Main setup process
main() {
    log_info "ITDO ERP v2 - Production Setup"
    echo "=============================="
    echo
    
    # Get configuration
    get_input "Enter your domain name (e.g., erp.company.com)" DOMAIN
    get_input "Enter database password" DB_PASSWORD
    get_input "Enter JWT secret key (leave empty to generate)" JWT_SECRET ""
    get_input "Enter admin email" ADMIN_EMAIL
    get_input "Enter admin password" ADMIN_PASSWORD
    
    # Generate secrets if needed
    if [[ -z "$JWT_SECRET" ]]; then
        JWT_SECRET=$(generate_password)
        log_info "Generated JWT secret: $JWT_SECRET"
    fi
    
    SECRET_KEY=$(generate_password)
    log_info "Generated secret key: $SECRET_KEY"
    
    # Create application user
    log_info "Creating application user..."
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_USER"
        usermod -aG sudo "$APP_USER"
    else
        log_warn "User $APP_USER already exists"
    fi
    
    # Install system packages
    log_info "Installing system packages..."
    apt update
    apt install -y python3.13 python3.13-venv python3.13-dev \
        postgresql postgresql-client redis-server nginx certbot \
        python3-certbot-nginx git curl build-essential
    
    # Install uv for app user
    log_info "Installing uv package manager..."
    sudo -u "$APP_USER" bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    
    # Clone repository
    log_info "Setting up application..."
    if [[ ! -d "$APP_DIR" ]]; then
        sudo -u "$APP_USER" git clone https://github.com/yourusername/ITDO_ERP2.git "$APP_DIR"
    else
        log_warn "Application directory already exists"
    fi
    
    # Create database
    log_info "Setting up database..."
    sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
        CREATE DATABASE $DB_NAME OWNER $DB_USER;
    END IF;
    
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
END
\$\$;
EOF
    
    # Create environment file
    log_info "Creating environment configuration..."
    cat > "$APP_DIR/backend/.env.production" <<EOF
# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["https://${DOMAIN}"]

# Application
APP_NAME="ITDO ERP v2"
APP_VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Session
SESSION_TIMEOUT_MINUTES=480
SESSION_IDLE_TIMEOUT_MINUTES=30
SESSION_REMEMBER_ME_DAYS=30

# MFA
MFA_ISSUER_NAME="ITDO ERP"
MFA_ENFORCE_FOR_ADMIN=true
MFA_ENFORCE_FOR_EXTERNAL=true
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/backend/.env.production"
    chmod 600 "$APP_DIR/backend/.env.production"
    
    # Install application
    log_info "Installing application dependencies..."
    cd "$APP_DIR/backend"
    sudo -u "$APP_USER" /home/"$APP_USER"/.local/bin/uv sync --frozen
    
    # Run migrations
    log_info "Running database migrations..."
    sudo -u "$APP_USER" /home/"$APP_USER"/.local/bin/uv run alembic upgrade head
    
    # Create systemd service
    log_info "Creating systemd service..."
    cat > /etc/systemd/system/itdo-erp-backend.service <<EOF
[Unit]
Description=ITDO ERP Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=/home/$APP_USER/.local/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=/home/$APP_USER/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=append:/home/$APP_USER/logs/backend.log
StandardError=append:/home/$APP_USER/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Create log directory
    sudo -u "$APP_USER" mkdir -p "/home/$APP_USER/logs"
    
    # Configure nginx
    log_info "Configuring nginx..."
    cat > /etc/nginx/sites-available/itdo-erp <<EOF
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL configuration will be added by certbot
    
    client_max_body_size 10M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Frontend (when deployed)
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    
    # Enable nginx site
    ln -sf /etc/nginx/sites-available/itdo-erp /etc/nginx/sites-enabled/
    nginx -t
    systemctl reload nginx
    
    # Start services
    log_info "Starting services..."
    systemctl daemon-reload
    systemctl enable itdo-erp-backend
    systemctl start itdo-erp-backend
    
    # Create admin user
    log_info "Creating admin user..."
    cd "$APP_DIR/backend"
    sudo -u "$APP_USER" /home/"$APP_USER"/.local/bin/uv run python -c "
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

db: Session = next(get_db())
admin = User(
    email='$ADMIN_EMAIL',
    username='admin',
    hashed_password=get_password_hash('$ADMIN_PASSWORD'),
    full_name='System Administrator',
    is_active=True,
    is_superuser=True,
    is_verified=True
)
db.add(admin)
db.commit()
print('Admin user created successfully')
"
    
    # Setup SSL
    log_info "Setting up SSL certificate..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$ADMIN_EMAIL"
    
    # Final checks
    log_info "Running final checks..."
    systemctl status itdo-erp-backend --no-pager
    
    log_info "Setup complete!"
    echo
    echo "Next steps:"
    echo "1. Configure your DNS to point $DOMAIN to this server"
    echo "2. Set up Google OAuth credentials and update .env.production"
    echo "3. Configure Keycloak if using external authentication"
    echo "4. Set up monitoring and backups"
    echo "5. Test the application at https://$DOMAIN"
    echo
    echo "Admin credentials:"
    echo "  Email: $ADMIN_EMAIL"
    echo "  Password: $ADMIN_PASSWORD"
    echo
    echo "Important: Save these credentials securely!"
}

# Check if running as root
check_root

# Run main setup
main "$@"