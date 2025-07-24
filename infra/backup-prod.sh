#!/bin/bash
# ITDO ERP v2 - Production Backup Script
# Automated database and application data backup

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="itdo_erp"
POSTGRES_USER="itdo_user"
REDIS_HOST="redis"
REDIS_PORT="6379"

# Backup retention (days)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# AWS S3 configuration (optional)
S3_BUCKET=${S3_BACKUP_BUCKET:-""}
AWS_REGION=${AWS_REGION:-"ap-northeast-1"}

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_FOLDER=$(date +%Y/%m/%d)

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] BACKUP: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] BACKUP WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] BACKUP ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] BACKUP INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking backup prerequisites..."
    
    # Check if backup directory exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        info "Created backup directory: $BACKUP_DIR"
    fi
    
    # Check if PostgreSQL is accessible
    if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        error "PostgreSQL is not accessible at $POSTGRES_HOST:$POSTGRES_PORT"
    fi
    
    # Check if Redis is accessible
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        warn "Redis is not accessible at $REDIS_HOST:$REDIS_PORT - skipping Redis backup"
        REDIS_AVAILABLE=false
    else
        REDIS_AVAILABLE=true
    fi
    
    # Check disk space (require at least 1GB free)
    AVAILABLE_SPACE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 1048576 ]]; then
        error "Insufficient disk space. Available: ${AVAILABLE_SPACE}KB, Required: 1GB"
    fi
    
    log "Prerequisites check completed"
}

# Create daily backup directory
create_backup_structure() {
    DAILY_BACKUP_DIR="$BACKUP_DIR/$DATE_FOLDER"
    mkdir -p "$DAILY_BACKUP_DIR"
    
    # Create backup metadata
    cat > "$DAILY_BACKUP_DIR/backup_info.txt" << EOF
ITDO ERP v2 Production Backup
=============================
Backup Date: $(date)
Backup Type: Full
Database: $POSTGRES_DB
Host: $POSTGRES_HOST
User: $POSTGRES_USER
Retention: $RETENTION_DAYS days
EOF
    
    info "Created backup directory structure: $DAILY_BACKUP_DIR"
}

# Backup PostgreSQL database
backup_postgresql() {
    log "Starting PostgreSQL database backup..."
    
    local backup_file="$DAILY_BACKUP_DIR/postgresql_${TIMESTAMP}.sql"
    local backup_custom="$DAILY_BACKUP_DIR/postgresql_${TIMESTAMP}.custom"
    
    # Create SQL dump
    info "Creating PostgreSQL SQL dump..."
    if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --verbose --clean --if-exists --create --format=plain > "$backup_file" 2>/dev/null; then
        
        # Compress SQL dump
        gzip "$backup_file"
        info "PostgreSQL SQL dump created and compressed: ${backup_file}.gz"
    else
        error "Failed to create PostgreSQL SQL dump"
    fi
    
    # Create custom format dump (for faster restoration)
    info "Creating PostgreSQL custom format dump..."
    if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --verbose --format=custom --compress=9 > "$backup_custom" 2>/dev/null; then
        info "PostgreSQL custom format dump created: $backup_custom"
    else
        warn "Failed to create PostgreSQL custom format dump"
    fi
    
    # Create database schema only backup
    local schema_file="$DAILY_BACKUP_DIR/postgresql_schema_${TIMESTAMP}.sql"
    if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        --schema-only --verbose > "$schema_file" 2>/dev/null; then
        gzip "$schema_file"
        info "PostgreSQL schema backup created: ${schema_file}.gz"
    else
        warn "Failed to create PostgreSQL schema backup"
    fi
    
    # Verify backup integrity
    if [[ -f "${backup_file}.gz" ]]; then
        if gunzip -t "${backup_file}.gz" >/dev/null 2>&1; then
            log "PostgreSQL backup integrity verified"
        else
            error "PostgreSQL backup integrity check failed"
        fi
    fi
    
    log "PostgreSQL backup completed successfully"
}

# Backup Redis data
backup_redis() {
    if [[ "$REDIS_AVAILABLE" == "true" ]]; then
        log "Starting Redis data backup..."
        
        local backup_file="$DAILY_BACKUP_DIR/redis_${TIMESTAMP}.rdb"
        
        # Create Redis backup using BGSAVE
        info "Creating Redis RDB backup..."
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$backup_file" >/dev/null 2>&1; then
            
            # Compress Redis backup
            gzip "$backup_file"
            info "Redis backup created and compressed: ${backup_file}.gz"
            
            # Verify backup
            if [[ -f "${backup_file}.gz" ]]; then
                log "Redis backup completed successfully"
            else
                warn "Redis backup file not found after compression"
            fi
        else
            warn "Failed to create Redis backup"
        fi
    else
        info "Skipping Redis backup - service not available"
    fi
}

# Backup application logs
backup_logs() {
    log "Starting application logs backup..."
    
    local logs_backup="$DAILY_BACKUP_DIR/application_logs_${TIMESTAMP}.tar.gz"
    
    # Find and backup recent logs (last 7 days)
    find /var/log -name "*.log" -mtime -7 -type f 2>/dev/null | \
    tar -czf "$logs_backup" --files-from=- 2>/dev/null || true
    
    if [[ -f "$logs_backup" ]] && [[ -s "$logs_backup" ]]; then
        info "Application logs backup created: $logs_backup"
    else
        info "No recent application logs found to backup"
        rm -f "$logs_backup" 2>/dev/null || true
    fi
    
    log "Application logs backup completed"
}

# Backup configuration files
backup_configurations() {
    log "Starting configuration files backup..."
    
    local config_backup="$DAILY_BACKUP_DIR/configurations_${TIMESTAMP}.tar.gz"
    
    # Create temporary directory for config files
    local temp_config_dir="/tmp/itdo_config_backup"
    mkdir -p "$temp_config_dir"
    
    # Copy important configuration files
    cp /etc/postgresql/postgresql.conf "$temp_config_dir/" 2>/dev/null || true
    cp /etc/nginx/nginx.conf "$temp_config_dir/" 2>/dev/null || true
    cp /etc/redis/redis.conf "$temp_config_dir/" 2>/dev/null || true
    
    # Copy application environment files (excluding sensitive data)
    if [[ -f "/.env.prod" ]]; then
        # Create sanitized version without passwords
        grep -v "PASSWORD\|SECRET\|KEY" /.env.prod > "$temp_config_dir/env.prod.sanitized" 2>/dev/null || true
    fi
    
    # Create configuration backup
    if [[ -n "$(ls -A "$temp_config_dir" 2>/dev/null)" ]]; then
        tar -czf "$config_backup" -C "$temp_config_dir" . 2>/dev/null
        info "Configuration files backup created: $config_backup"
    else
        info "No configuration files found to backup"
    fi
    
    # Cleanup
    rm -rf "$temp_config_dir"
    
    log "Configuration files backup completed"
}

# Upload to S3 (if configured)
upload_to_s3() {
    if [[ -n "$S3_BUCKET" ]] && command -v aws >/dev/null 2>&1; then
        log "Starting S3 upload..."
        
        local s3_path="s3://$S3_BUCKET/itdo-erp-backups/$DATE_FOLDER/"
        
        # Upload backup files to S3
        if aws s3 sync "$DAILY_BACKUP_DIR" "$s3_path" --region "$AWS_REGION" --quiet; then
            info "Backup uploaded to S3: $s3_path"
            
            # Tag the backup
            aws s3api put-object-tagging \
                --bucket "$S3_BUCKET" \
                --key "itdo-erp-backups/$DATE_FOLDER/backup_info.txt" \
                --tagging "TagSet=[{Key=BackupDate,Value=$(date +%Y-%m-%d)},{Key=Application,Value=ITDO-ERP},{Key=Type,Value=DatabaseBackup}]" \
                --region "$AWS_REGION" >/dev/null 2>&1 || true
                
            log "S3 upload completed successfully"
        else
            warn "Failed to upload backup to S3"
        fi
    else
        info "S3 upload skipped - AWS CLI not configured or S3_BUCKET not set"
    fi
}

# Generate backup report
generate_report() {
    log "Generating backup report..."
    
    local report_file="$DAILY_BACKUP_DIR/backup_report_${TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
ITDO ERP v2 Backup Report
========================
Date: $(date)
Backup Directory: $DAILY_BACKUP_DIR
Retention Period: $RETENTION_DAYS days

Backup Files:
$(ls -lah "$DAILY_BACKUP_DIR" | grep -v "^total\|^d" | awk '{print $9 "\t" $5 "\t" $6 " " $7 " " $8}')

Database Status:
- PostgreSQL: $(pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>&1)
- Redis: $(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null || echo "Not available")

System Information:
- Disk Usage: $(df -h "$BACKUP_DIR" | awk 'NR==2 {print "Used: " $3 ", Available: " $4 ", Usage: " $5}')
- Memory Usage: $(free -h | awk 'NR==2{print "Used: " $3 ", Available: " $7}')
- Load Average: $(uptime | awk -F'load average:' '{print $2}')

S3 Upload: $(if [[ -n "$S3_BUCKET" ]]; then echo "Configured to: $S3_BUCKET"; else echo "Not configured"; fi)

Backup Integrity:
$(find "$DAILY_BACKUP_DIR" -name "*.gz" -exec echo "Checking: {}" \; -exec gunzip -t {} \; 2>&1 | tail -10)

EOF
    
    info "Backup report generated: $report_file"
    
    # Display summary
    echo -e "\n${BLUE}=== Backup Summary ===${NC}"
    echo "Date: $(date)"
    echo "Location: $DAILY_BACKUP_DIR"
    echo "Files created: $(find "$DAILY_BACKUP_DIR" -type f | wc -l)"
    echo "Total size: $(du -sh "$DAILY_BACKUP_DIR" | cut -f1)"
    echo "S3 upload: $(if [[ -n "$S3_BUCKET" ]]; then echo "Yes"; else echo "No"; fi)"
    
    log "Backup report completed"
}

# Clean old backups
cleanup_old_backups() {
    log "Starting cleanup of old backups..."
    
    # Find and remove backups older than retention period
    local deleted_count=0
    
    find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS | while read -r old_backup; do
        if [[ -d "$old_backup" ]]; then
            info "Removing old backup: $old_backup"
            rm -rf "$old_backup"
            ((deleted_count++))
        fi
    done
    
    # Clean S3 old backups if configured
    if [[ -n "$S3_BUCKET" ]] && command -v aws >/dev/null 2>&1; then
        local cutoff_date=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d)
        info "Cleaning S3 backups older than $cutoff_date"
        
        aws s3 ls "s3://$S3_BUCKET/itdo-erp-backups/" --recursive --region "$AWS_REGION" | \
        awk -v cutoff="$cutoff_date" '$1 < cutoff {print $4}' | \
        while read -r old_file; do
            aws s3 rm "s3://$S3_BUCKET/$old_file" --region "$AWS_REGION" --quiet || true
        done
    fi
    
    info "Old backups cleanup completed"
    log "Cleanup process finished"
}

# Health check - verify backup can be restored
health_check() {
    log "Performing backup health check..."
    
    # Check if latest backup files exist and are readable
    local latest_sql=$(find "$DAILY_BACKUP_DIR" -name "postgresql_*.sql.gz" -type f | head -1)
    local latest_custom=$(find "$DAILY_BACKUP_DIR" -name "postgresql_*.custom" -type f | head -1)
    
    if [[ -f "$latest_sql" ]]; then
        if gunzip -t "$latest_sql" >/dev/null 2>&1; then
            info "SQL backup integrity verified: $latest_sql"
        else
            error "SQL backup integrity check failed: $latest_sql"
        fi
    fi
    
    if [[ -f "$latest_custom" ]]; then
        # Test custom format with pg_restore
        if pg_restore --list "$latest_custom" >/dev/null 2>&1; then
            info "Custom backup integrity verified: $latest_custom"
        else
            warn "Custom backup integrity check failed: $latest_custom"
        fi
    fi
    
    log "Backup health check completed"
}

# Send notification (placeholder for integration with monitoring systems)
send_notification() {
    local status=$1
    local message=$2
    
    # Log the notification (in production, integrate with Slack, email, etc.)
    if [[ "$status" == "success" ]]; then
        log "NOTIFICATION: $message"
    else
        error "NOTIFICATION: $message"
    fi
    
    # Placeholder for webhook notification
    # curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
    #   -d "{\"text\":\"ITDO ERP Backup $status: $message\"}" || true
}

# Main backup function
main() {
    local start_time=$(date +%s)
    
    log "Starting ITDO ERP v2 production backup process..."
    
    # Trap for cleanup on exit
    trap 'cleanup_on_exit $?' EXIT
    
    # Execute backup steps
    check_prerequisites
    create_backup_structure
    backup_postgresql
    backup_redis
    backup_logs
    backup_configurations
    upload_to_s3
    generate_report
    health_check
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "Backup process completed successfully in ${duration} seconds"
    send_notification "success" "Backup completed in ${duration}s - Location: $DAILY_BACKUP_DIR"
}

# Cleanup function
cleanup_on_exit() {
    local exit_code=$1
    
    if [[ $exit_code -ne 0 ]]; then
        error "Backup process failed with exit code: $exit_code"
        send_notification "failed" "Backup process failed with exit code: $exit_code"
    fi
    
    # Clean up temporary files
    rm -rf /tmp/itdo_config_backup 2>/dev/null || true
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi