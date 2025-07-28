#!/bin/bash
#
# Database backup script for ITDO ERP v2
# This script creates compressed backups of the PostgreSQL database
#

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/itdo-erp/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-itdo_erp_prod}"
DB_USER="${DB_USER:-itdo_erp}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/itdo_erp_backup_${TIMESTAMP}.sql.gz"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    log_info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Start backup
log_info "Starting database backup for $DB_NAME"
log_info "Backup file: $BACKUP_FILE"

# Perform the backup
if PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-privileges \
    --format=plain \
    --exclude-schema=pglogical \
    --exclude-schema=pglogical_origin | gzip -9 > "$BACKUP_FILE"; then
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup completed successfully. Size: $BACKUP_SIZE"
    
    # Verify the backup
    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        log_info "Backup verification passed"
    else
        log_error "Backup verification failed - backup may be corrupted"
        exit 1
    fi
    
    # Clean up old backups
    log_info "Cleaning up backups older than $RETENTION_DAYS days"
    DELETED_COUNT=$(find "$BACKUP_DIR" -name "itdo_erp_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$DELETED_COUNT" -gt 0 ]; then
        log_info "Deleted $DELETED_COUNT old backup(s)"
    fi
    
    # List current backups
    log_info "Current backups:"
    ls -lh "$BACKUP_DIR"/itdo_erp_backup_*.sql.gz | tail -5
    
    # Create a latest symlink
    ln -sf "$BACKUP_FILE" "$BACKUP_DIR/itdo_erp_latest.sql.gz"
    log_info "Created symlink: itdo_erp_latest.sql.gz"
    
else
    log_error "Backup failed"
    exit 1
fi

# Optional: Upload to cloud storage
if [ "${UPLOAD_TO_S3:-false}" = "true" ] && command -v aws &> /dev/null; then
    log_info "Uploading backup to S3"
    if aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/database-backups/" --storage-class STANDARD_IA; then
        log_info "Upload to S3 completed"
    else
        log_warn "Upload to S3 failed"
    fi
fi

# Send notification (if configured)
if [ -n "${SLACK_WEBHOOK:-}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Database backup completed successfully\\nDatabase: $DB_NAME\\nSize: $BACKUP_SIZE\\nFile: $(basename $BACKUP_FILE)\"}" \
        "$SLACK_WEBHOOK" 2>/dev/null || log_warn "Failed to send Slack notification"
fi

log_info "Backup process completed"