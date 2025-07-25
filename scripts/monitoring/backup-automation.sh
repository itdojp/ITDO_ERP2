#!/bin/bash
# ITDO ERP v2 - Automated Backup System
# CC03 v58.0 - Day 2 Infrastructure Automation
# RTO: 15 minutes, RPO: 1 hour

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_BASE_DIR="/opt/itdo-erp/backups"
LOG_FILE="/var/log/itdo-erp/backup.log"
RETENTION_DAYS=30
FULL_BACKUP_HOUR=2  # 2 AM
INCREMENTAL_BACKUP_INTERVAL=60  # minutes

# AWS S3 Configuration (optional)
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"

# Notification Configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENT="${BACKUP_ALERT_EMAIL:-}"

# Compose Configuration
COMPOSE_FILE="${PROJECT_ROOT}/infra/compose-prod.yaml"
ENV_FILE="${PROJECT_ROOT}/infra/.env.prod"
COMPOSE_CMD=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Initialize backup environment
init_backup_system() {
    log "🔧 Initializing automated backup system..."
    
    # Create backup directories
    mkdir -p "$BACKUP_BASE_DIR"/{database,files,configs,logs}
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Detect container engine
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        error "No container orchestration tool found"
        exit 1
    fi
    
    # Install required tools
    install_backup_tools
    
    log "✅ Backup system initialized"
}

# Install required backup tools
install_backup_tools() {
    log "Installing backup tools..."
    
    # Install AWS CLI if S3 backup is configured
    if [[ -n "$S3_BUCKET" ]] && ! command -v aws &> /dev/null; then
        info "Installing AWS CLI for S3 backups..."
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip -q awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    fi
    
    # Install compression tools
    if ! command -v pigz &> /dev/null; then
        info "Installing pigz for parallel compression..."
        sudo apt-get update && sudo apt-get install -y pigz
    fi
    
    # Install encryption tools
    if ! command -v gpg &> /dev/null; then
        info "Installing GPG for backup encryption..."
        sudo apt-get update && sudo apt-get install -y gnupg
    fi
    
    log "✅ Backup tools installed"
}

# Database backup
backup_database() {
    local backup_type="${1:-full}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$BACKUP_BASE_DIR/database/$timestamp"
    
    log "📊 Starting database backup (type: $backup_type)..."
    
    mkdir -p "$backup_dir"
    
    # Check if database is running
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps postgres | grep -q "Up"; then
        warn "PostgreSQL container is not running - skipping database backup"
        return 0
    fi
    
    # Get database connection info
    local db_host="localhost"
    local db_port="5432"
    local db_name="itdo_erp"
    local db_user="itdo_user"
    local db_password
    db_password=$(grep "POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"')
    
    # Full database backup
    if [[ "$backup_type" == "full" ]]; then
        log "Creating full database backup..."
        
        export PGPASSWORD="$db_password"
        
        # Create full backup with custom format for faster restore
        if pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
            --format=custom --compress=9 --verbose \
            --file="$backup_dir/database_full.dump" 2>> "$LOG_FILE"; then
            
            log "✅ Full database backup completed"
            
            # Create SQL format backup for compatibility
            pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
                --format=plain --verbose \
                --file="$backup_dir/database_full.sql" 2>> "$LOG_FILE"
            
            # Compress SQL backup
            pigz -9 "$backup_dir/database_full.sql"
            
        else
            error "❌ Database backup failed"
            return 1
        fi
        
        unset PGPASSWORD
        
    # Incremental backup (WAL files)
    else
        log "Creating incremental database backup (WAL files)..."
        
        # Copy WAL files
        if $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
            find /var/lib/postgresql/data/pg_wal -name "*.backup" -o -name "*[0-9A-F]" | \
            xargs -I {} cp {} "$backup_dir/" 2>/dev/null; then
            
            log "✅ Incremental database backup completed"
        else
            warn "No WAL files found for incremental backup"
        fi
    fi
    
    # Generate backup metadata
    cat > "$backup_dir/metadata.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_type": "$backup_type",
  "database": "$db_name",
  "size_bytes": $(du -sb "$backup_dir" | cut -f1),
  "files": $(find "$backup_dir" -type f | wc -l),
  "retention_until": "$(date -d "+${RETENTION_DAYS} days" -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    # Encrypt backups if GPG key is available
    if [[ -n "${BACKUP_GPG_KEY:-}" ]]; then
        encrypt_backup "$backup_dir"
    fi
    
    # Upload to S3 if configured
    if [[ -n "$S3_BUCKET" ]]; then
        upload_to_s3 "$backup_dir" "database/$timestamp"
    fi
    
    log "📊 Database backup completed: $backup_dir"
    echo "$backup_dir"
}

# Files backup (uploads, logs, configs)
backup_files() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$BACKUP_BASE_DIR/files/$timestamp"
    
    log "📁 Starting files backup..."
    
    mkdir -p "$backup_dir"
    
    # Backup application uploads
    if [[ -d "/opt/itdo-erp/data/uploads" ]]; then
        log "Backing up application uploads..."
        tar -czf "$backup_dir/uploads.tar.gz" -C "/opt/itdo-erp/data" uploads/ 2>/dev/null || true
    fi
    
    # Backup logs
    if [[ -d "/opt/itdo-erp/logs" ]]; then
        log "Backing up application logs..."
        tar -czf "$backup_dir/logs.tar.gz" -C "/opt/itdo-erp" logs/ 2>/dev/null || true
    fi
    
    # Backup configuration files
    log "Backing up configuration files..."
    mkdir -p "$backup_dir/configs"
    cp "$COMPOSE_FILE" "$backup_dir/configs/" 2>/dev/null || true
    cp "$ENV_FILE" "$backup_dir/configs/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/infra/nginx" "$backup_dir/configs/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/infra/postgres" "$backup_dir/configs/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/infra/redis" "$backup_dir/configs/" 2>/dev/null || true
    
    # Generate backup metadata
    cat > "$backup_dir/metadata.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_type": "files",
  "size_bytes": $(du -sb "$backup_dir" | cut -f1),
  "files": $(find "$backup_dir" -type f | wc -l),
  "retention_until": "$(date -d "+${RETENTION_DAYS} days" -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    # Encrypt and upload
    if [[ -n "${BACKUP_GPG_KEY:-}" ]]; then
        encrypt_backup "$backup_dir"
    fi
    
    if [[ -n "$S3_BUCKET" ]]; then
        upload_to_s3 "$backup_dir" "files/$timestamp"
    fi
    
    log "📁 Files backup completed: $backup_dir"
    echo "$backup_dir"
}

# Container state backup
backup_container_state() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$BACKUP_BASE_DIR/containers/$timestamp"
    
    log "🐳 Starting container state backup..."
    
    mkdir -p "$backup_dir"
    
    # Export container configurations
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config > "$backup_dir/docker-compose-resolved.yaml"
    
    # Save running container list
    $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --format json > "$backup_dir/containers-status.json" 2>/dev/null || echo "[]" > "$backup_dir/containers-status.json"
    
    # Save Docker/Podman volumes info
    if command -v docker &> /dev/null; then
        docker volume ls --format json > "$backup_dir/volumes.json" 2>/dev/null || echo "[]" > "$backup_dir/volumes.json"
    elif command -v podman &> /dev/null; then
        podman volume ls --format json > "$backup_dir/volumes.json" 2>/dev/null || echo "[]" > "$backup_dir/volumes.json"
    fi
    
    log "🐳 Container state backup completed: $backup_dir"
    echo "$backup_dir"
}

# Encrypt backup directory
encrypt_backup() {
    local backup_dir="$1"
    
    log "🔐 Encrypting backup: $(basename "$backup_dir")"
    
    # Create encrypted archive
    tar -czf - -C "$(dirname "$backup_dir")" "$(basename "$backup_dir")" | \
        gpg --cipher-algo AES256 --compress-algo 2 --symmetric \
            --output "${backup_dir}.tar.gz.gpg" \
            --batch --yes --passphrase "${BACKUP_GPG_PASSPHRASE:-itdo-erp-backup-2025}"
    
    # Verify encryption
    if [[ -f "${backup_dir}.tar.gz.gpg" ]]; then
        log "✅ Backup encrypted successfully"
        # Remove unencrypted version
        rm -rf "$backup_dir"
    else
        error "❌ Backup encryption failed"
        return 1
    fi
}

# Upload backup to S3
upload_to_s3() {
    local local_path="$1"
    local s3_path="$2"
    
    log "☁️ Uploading backup to S3: s3://$S3_BUCKET/$s3_path"
    
    if [[ -d "$local_path" ]]; then
        # Upload directory
        if aws s3 sync "$local_path" "s3://$S3_BUCKET/$s3_path" \
            --region "$S3_REGION" \
            --storage-class STANDARD_IA \
            --server-side-encryption AES256; then
            log "✅ Backup uploaded to S3 successfully"
        else
            error "❌ S3 upload failed"
            return 1
        fi
    elif [[ -f "$local_path" ]]; then
        # Upload single file
        if aws s3 cp "$local_path" "s3://$S3_BUCKET/$s3_path" \
            --region "$S3_REGION" \
            --storage-class STANDARD_IA \
            --server-side-encryption AES256; then
            log "✅ Encrypted backup uploaded to S3 successfully"
        else
            error "❌ S3 upload failed"
            return 1
        fi
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "🧹 Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    # Local cleanup
    find "$BACKUP_BASE_DIR" -type d -name "[0-9]*_[0-9]*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    find "$BACKUP_BASE_DIR" -type f -name "*.tar.gz.gpg" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # S3 cleanup if configured
    if [[ -n "$S3_BUCKET" ]]; then
        log "Cleaning up old S3 backups..."
        aws s3api list-objects-v2 --bucket "$S3_BUCKET" --query 'Contents[?LastModified<`'"$(date -d "-${RETENTION_DAYS} days" --iso-8601)"'`].[Key]' --output text | \
        while read -r key; do
            if [[ -n "$key" && "$key" != "None" ]]; then
                aws s3 rm "s3://$S3_BUCKET/$key"
                log "Deleted old S3 backup: $key"
            fi
        done
    fi
    
    log "✅ Old backups cleaned up"
}

# Verify backup integrity
verify_backup() {
    local backup_path="$1"
    
    log "🔍 Verifying backup integrity: $(basename "$backup_path")"
    
    if [[ -d "$backup_path" ]]; then
        # Check if all expected files exist
        local has_database=false
        local has_metadata=false
        
        [[ -f "$backup_path/database_full.dump" || -f "$backup_path/database_full.sql.gz" ]] && has_database=true
        [[ -f "$backup_path/metadata.json" ]] && has_metadata=true
        
        if [[ "$has_database" == "true" && "$has_metadata" == "true" ]]; then
            log "✅ Backup integrity verified"
            return 0
        else
            error "❌ Backup integrity check failed"
            return 1
        fi
    elif [[ -f "$backup_path" && "$backup_path" == *.gpg ]]; then
        # Verify encrypted backup
        if gpg --batch --yes --passphrase "${BACKUP_GPG_PASSPHRASE:-itdo-erp-backup-2025}" \
            --decrypt "$backup_path" > /dev/null 2>&1; then
            log "✅ Encrypted backup integrity verified"
            return 0
        else
            error "❌ Encrypted backup integrity check failed"
            return 1
        fi
    else
        error "❌ Backup path not found or invalid: $backup_path"
        return 1
    fi
}

# Send backup notification
send_notification() {
    local status="$1"
    local message="$2"
    local backup_size="${3:-0}"
    
    # Slack notification
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        [[ "$status" == "error" ]] && color="danger"
        [[ "$status" == "warning" ]] && color="warning"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"ITDO ERP Backup Report\",
                    \"text\": \"$message\",
                    \"fields\": [{
                        \"title\": \"Backup Size\",
                        \"value\": \"$(numfmt --to=iec $backup_size)\",
                        \"short\": true
                    }, {
                        \"title\": \"Retention\",
                        \"value\": \"${RETENTION_DAYS} days\",
                        \"short\": true
                    }],
                    \"footer\": \"Backup Automation System\",
                    \"ts\": $(date +%s)
                }]
            }" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
    
    # Email notification
    if [[ -n "$EMAIL_RECIPIENT" ]] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "ITDO ERP Backup Report - $status" "$EMAIL_RECIPIENT" 2>/dev/null || true
    fi
}

# Main backup orchestration
run_full_backup() {
    local start_time=$(date +%s)
    log "🚀 Starting full backup process..."
    
    local backup_paths=()
    local total_size=0
    local success=true
    
    # Database backup
    if db_backup_path=$(backup_database "full"); then
        backup_paths+=("$db_backup_path")
        total_size=$((total_size + $(du -sb "$db_backup_path" 2>/dev/null | cut -f1 || echo 0)))
    else
        success=false
    fi
    
    # Files backup
    if files_backup_path=$(backup_files); then
        backup_paths+=("$files_backup_path")
        total_size=$((total_size + $(du -sb "$files_backup_path" 2>/dev/null | cut -f1 || echo 0)))
    else
        success=false
    fi
    
    # Container state backup
    if container_backup_path=$(backup_container_state); then
        backup_paths+=("$container_backup_path")
        total_size=$((total_size + $(du -sb "$container_backup_path" 2>/dev/null | cut -f1 || echo 0)))
    else
        success=false
    fi
    
    # Verify all backups
    for backup_path in "${backup_paths[@]}"; do
        if ! verify_backup "$backup_path"; then
            success=false
        fi
    done
    
    # Cleanup old backups
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Send notification
    if [[ "$success" == "true" ]]; then
        local message="✅ Full backup completed successfully in ${duration}s"
        log "$message"
        send_notification "success" "$message" "$total_size"
    else
        local message="❌ Backup completed with errors in ${duration}s"
        error "$message"
        send_notification "error" "$message" "$total_size"
    fi
    
    log "🎉 Full backup process completed"
}

# Incremental backup
run_incremental_backup() {
    log "🔄 Starting incremental backup..."
    
    local backup_path
    if backup_path=$(backup_database "incremental"); then
        local backup_size
        backup_size=$(du -sb "$backup_path" 2>/dev/null | cut -f1 || echo 0)
        log "✅ Incremental backup completed"
        send_notification "success" "Incremental backup completed" "$backup_size"
    else
        error "❌ Incremental backup failed"
        send_notification "error" "Incremental backup failed" "0"
    fi
}

# Backup scheduler
schedule_backups() {
    log "📅 Starting backup scheduler..."
    
    # Add cron jobs for automated backups
    (crontab -l 2>/dev/null; echo "0 $FULL_BACKUP_HOUR * * * $0 full >/dev/null 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "*/$INCREMENTAL_BACKUP_INTERVAL * * * * $0 incremental >/dev/null 2>&1") | crontab -
    
    log "✅ Backup scheduler configured"
    log "  Full backup: Daily at ${FULL_BACKUP_HOUR}:00"
    log "  Incremental backup: Every ${INCREMENTAL_BACKUP_INTERVAL} minutes"
}

# Main function
main() {
    case "${1:-help}" in
        "full")
            init_backup_system
            run_full_backup
            ;;
        "incremental")
            init_backup_system
            run_incremental_backup
            ;;
        "files")
            init_backup_system
            backup_files
            ;;
        "database")
            init_backup_system
            backup_database "full"
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "schedule")
            init_backup_system
            schedule_backups
            ;;
        "verify")
            [[ -n "${2:-}" ]] || { error "Usage: $0 verify <backup_path>"; exit 1; }
            verify_backup "$2"
            ;;
        *)
            echo "ITDO ERP v2 - Automated Backup System"
            echo "Usage: $0 {full|incremental|files|database|cleanup|schedule|verify}"
            echo ""
            echo "Commands:"
            echo "  full        - Run full backup (database + files + config)"
            echo "  incremental - Run incremental database backup"
            echo "  files       - Backup files and configurations only"
            echo "  database    - Backup database only"
            echo "  cleanup     - Remove old backups beyond retention period"
            echo "  schedule    - Install cron jobs for automated backups"
            echo "  verify PATH - Verify backup integrity"
            echo ""
            echo "Configuration:"
            echo "  BACKUP_S3_BUCKET     - S3 bucket for remote backups"
            echo "  SLACK_WEBHOOK_URL    - Slack webhook for notifications"
            echo "  BACKUP_ALERT_EMAIL   - Email for backup notifications"
            echo "  BACKUP_GPG_KEY       - GPG key for backup encryption"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"