#!/bin/bash
# ITDO ERP v2 - Production Backup Script
# CC03 v59.0 - Practical Production Infrastructure

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET=${S3_BUCKET:-""}

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

# Database backup
backup_database() {
    log "Starting database backup..."
    
    local backup_file="${BACKUP_DIR}/postgres/db_backup_${TIMESTAMP}.sql"
    mkdir -p "$(dirname "$backup_file")"
    
    if pg_dump -h postgres -U itdo_user -d itdo_erp > "$backup_file"; then
        log "Database backup completed: $backup_file"
        
        # Compress backup
        gzip "$backup_file"
        log "Database backup compressed: ${backup_file}.gz"
    else
        error "Database backup failed"
        return 1
    fi
}

# Redis backup
backup_redis() {
    log "Starting Redis backup..."
    
    local backup_file="${BACKUP_DIR}/redis/redis_backup_${TIMESTAMP}.rdb"
    mkdir -p "$(dirname "$backup_file")"
    
    # Save Redis state
    if redis-cli -h redis -a "$REDIS_PASSWORD" BGSAVE; then
        # Wait for background save to complete
        while [[ $(redis-cli -h redis -a "$REDIS_PASSWORD" LASTSAVE) == $(redis-cli -h redis -a "$REDIS_PASSWORD" LASTSAVE) ]]; do
            sleep 1
        done
        
        # Copy the dump file
        if redis-cli -h redis -a "$REDIS_PASSWORD" --rdb "$backup_file"; then
            log "Redis backup completed: $backup_file"
        else
            error "Redis backup failed"
            return 1
        fi
    else
        error "Redis BGSAVE failed"
        return 1
    fi
}

# Application data backup
backup_app_data() {
    log "Starting application data backup..."
    
    local backup_file="${BACKUP_DIR}/app/app_data_${TIMESTAMP}.tar.gz"
    mkdir -p "$(dirname "$backup_file")"
    
    # Backup application logs and data
    if tar -czf "$backup_file" -C /app data logs 2>/dev/null; then
        log "Application data backup completed: $backup_file"
    else
        warn "Application data backup completed with warnings"
    fi
}

# Upload to S3
upload_to_s3() {
    if [[ -n "$S3_BUCKET" ]]; then
        log "Uploading backups to S3..."
        
        local backup_date=$(date +%Y%m%d)
        
        # Upload each backup type
        if command -v aws &> /dev/null; then
            aws s3 sync "${BACKUP_DIR}/postgres" "s3://${S3_BUCKET}/postgres/${backup_date}/" --storage-class STANDARD_IA
            aws s3 sync "${BACKUP_DIR}/redis" "s3://${S3_BUCKET}/redis/${backup_date}/" --storage-class STANDARD_IA  
            aws s3 sync "${BACKUP_DIR}/app" "s3://${S3_BUCKET}/app/${backup_date}/" --storage-class STANDARD_IA
            
            log "S3 upload completed"
        else
            warn "AWS CLI not available, skipping S3 upload"
        fi
    else
        log "No S3 bucket configured, skipping cloud backup"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
    
    find "${BACKUP_DIR}" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    
    # Clean up empty directories
    find "${BACKUP_DIR}" -type d -empty -delete 2>/dev/null || true
    
    log "Old backup cleanup completed"
}

# Verify backup integrity
verify_backups() {
    log "Verifying backup integrity..."
    
    local postgres_backup=$(find "${BACKUP_DIR}/postgres" -name "*${TIMESTAMP}*" -type f | head -1)
    local redis_backup=$(find "${BACKUP_DIR}/redis" -name "*${TIMESTAMP}*" -type f | head -1)
    local app_backup=$(find "${BACKUP_DIR}/app" -name "*${TIMESTAMP}*" -type f | head -1)
    
    local verification_passed=true
    
    # Verify PostgreSQL backup
    if [[ -f "$postgres_backup" ]]; then
        if file "$postgres_backup" | grep -q "gzip"; then
            log "PostgreSQL backup verification: OK"
        else
            error "PostgreSQL backup verification: FAILED"
            verification_passed=false
        fi
    fi
    
    # Verify Redis backup
    if [[ -f "$redis_backup" ]]; then
        if file "$redis_backup" | grep -q "data"; then
            log "Redis backup verification: OK"
        else
            error "Redis backup verification: FAILED"
            verification_passed=false
        fi
    fi
    
    # Verify application backup
    if [[ -f "$app_backup" ]]; then
        if file "$app_backup" | grep -q "gzip"; then
            log "Application backup verification: OK"
        else
            error "Application backup verification: FAILED"
            verification_passed=false
        fi
    fi
    
    if [[ "$verification_passed" == "true" ]]; then
        log "All backup verifications passed"
        return 0
    else
        error "Some backup verifications failed"
        return 1
    fi
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        if [[ "$status" == "error" ]]; then
            color="danger"
        elif [[ "$status" == "warning" ]]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"ITDO ERP Backup Report\",
                    \"text\": \"$message\",
                    \"footer\": \"Backup System\",
                    \"ts\": $(date +%s)
                }]
            }" \
            "${SLACK_WEBHOOK_URL}" 2>/dev/null || true
    fi
}

# Main backup function
main() {
    local start_time=$(date +%s)
    log "Starting ITDO ERP production backup..."
    
    local backup_status="success"
    local error_messages=()
    
    # Create backup directory structure
    mkdir -p "${BACKUP_DIR}"/{postgres,redis,app}
    
    # Perform backups
    if ! backup_database; then
        backup_status="error"
        error_messages+=("Database backup failed")
    fi
    
    if ! backup_redis; then
        backup_status="error"
        error_messages+=("Redis backup failed")
    fi
    
    backup_app_data  # This can have warnings, don't fail on it
    
    # Verify backups
    if ! verify_backups; then
        backup_status="error"
        error_messages+=("Backup verification failed")
    fi
    
    # Upload to cloud storage
    upload_to_s3
    
    # Cleanup old backups
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Generate summary
    local summary_message="Backup completed in ${duration} seconds"
    if [[ "$backup_status" == "success" ]]; then
        log "$summary_message"
        send_notification "good" "✅ $summary_message"
    else
        error "$summary_message with errors: ${error_messages[*]}"
        send_notification "error" "❌ $summary_message with errors: ${error_messages[*]}"
        exit 1
    fi
    
    log "Backup process completed"
}

# Restore function
restore() {
    local backup_date=${1:-"latest"}
    
    log "Starting restore process for date: $backup_date"
    
    if [[ "$backup_date" == "latest" ]]; then
        local postgres_backup=$(find "${BACKUP_DIR}/postgres" -name "*.sql.gz" -type f | sort | tail -1)
        local redis_backup=$(find "${BACKUP_DIR}/redis" -name "*.rdb" -type f | sort | tail -1)
        local app_backup=$(find "${BACKUP_DIR}/app" -name "*.tar.gz" -type f | sort | tail -1)
    else
        local postgres_backup=$(find "${BACKUP_DIR}/postgres" -name "*${backup_date}*.sql.gz" -type f | head -1)
        local redis_backup=$(find "${BACKUP_DIR}/redis" -name "*${backup_date}*.rdb" -type f | head -1)
        local app_backup=$(find "${BACKUP_DIR}/app" -name "*${backup_date}*.tar.gz" -type f | head -1)
    fi
    
    # Restore database
    if [[ -f "$postgres_backup" ]]; then
        log "Restoring database from: $postgres_backup"
        zcat "$postgres_backup" | psql -h postgres -U itdo_user -d itdo_erp
        log "Database restore completed"
    else
        error "PostgreSQL backup not found for date: $backup_date"
    fi
    
    # Restore Redis
    if [[ -f "$redis_backup" ]]; then
        log "Restoring Redis from: $redis_backup"
        redis-cli -h redis -a "$REDIS_PASSWORD" FLUSHALL
        cat "$redis_backup" | redis-cli -h redis -a "$REDIS_PASSWORD" --pipe
        log "Redis restore completed"
    else
        error "Redis backup not found for date: $backup_date"
    fi
    
    # Restore application data
    if [[ -f "$app_backup" ]]; then
        log "Restoring application data from: $app_backup"
        tar -xzf "$app_backup" -C /app
        log "Application data restore completed"
    else
        warn "Application backup not found for date: $backup_date"
    fi
    
    log "Restore process completed"
}

# List available backups
list_backups() {
    log "Available backups:"
    
    echo "PostgreSQL backups:"
    find "${BACKUP_DIR}/postgres" -name "*.sql.gz" -type f | sort
    
    echo ""
    echo "Redis backups:"
    find "${BACKUP_DIR}/redis" -name "*.rdb" -type f | sort
    
    echo ""
    echo "Application backups:"
    find "${BACKUP_DIR}/app" -name "*.tar.gz" -type f | sort
}

# Usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backup              - Perform full backup (default)"
    echo "  restore [date]      - Restore from backup (latest if no date specified)"
    echo "  list                - List available backups"
    echo ""
    echo "Examples:"
    echo "  $0                  - Perform backup"
    echo "  $0 restore          - Restore from latest backup"
    echo "  $0 restore 20231225 - Restore from specific date"
    echo "  $0 list             - List all available backups"
}

# Main execution
case "${1:-backup}" in
    "backup")
        main
        ;;
    "restore")
        restore "${2:-latest}"
        ;;
    "list")
        list_backups
        ;;
    "--help"|"-h")
        usage
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac