#!/bin/bash
#
# Database restore script for ITDO ERP v2
# This script restores the PostgreSQL database from a backup
#

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/itdo-erp/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-itdo_erp_prod}"
DB_USER="${DB_USER:-itdo_erp}"
BACKUP_FILE=""

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

show_usage() {
    echo "Usage: $0 [options] <backup-file>"
    echo ""
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -d, --database       Database name (default: $DB_NAME)"
    echo "  -H, --host           Database host (default: $DB_HOST)"
    echo "  -p, --port           Database port (default: $DB_PORT)"
    echo "  -U, --user           Database user (default: $DB_USER)"
    echo "  -f, --force          Force restore without confirmation"
    echo "  --latest             Use the latest backup file"
    echo ""
    echo "Examples:"
    echo "  $0 --latest                                    # Restore from latest backup"
    echo "  $0 itdo_erp_backup_20240101_120000.sql.gz     # Restore specific backup"
    echo "  $0 -d test_db --force backup.sql.gz           # Restore to test database"
}

# Parse command line arguments
FORCE=false
USE_LATEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -H|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -U|--user)
            DB_USER="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --latest)
            USE_LATEST=true
            shift
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# Determine backup file
if [ "$USE_LATEST" = true ]; then
    BACKUP_FILE="$BACKUP_DIR/itdo_erp_latest.sql.gz"
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Latest backup symlink not found"
        exit 1
    fi
elif [ -z "$BACKUP_FILE" ]; then
    log_error "No backup file specified"
    show_usage
    exit 1
elif [ ! -f "$BACKUP_FILE" ]; then
    # Check if file exists in backup directory
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    else
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

# Show restore information
log_info "Database restore configuration:"
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  User: $DB_USER"
echo "  Backup file: $BACKUP_FILE"
echo "  Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "  Backup date: $(stat -c %y "$BACKUP_FILE" | cut -d' ' -f1)"

# Confirm restore
if [ "$FORCE" != true ]; then
    echo ""
    log_warn "This will DROP and RECREATE the database '$DB_NAME'"
    log_warn "All existing data will be PERMANENTLY DELETED"
    echo ""
    read -p "Are you sure you want to continue? Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
fi

# Create a pre-restore backup
if [ "$FORCE" != true ]; then
    log_info "Creating pre-restore backup of current database"
    PRE_RESTORE_BACKUP="$BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
    if PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-privileges | gzip -9 > "$PRE_RESTORE_BACKUP" 2>/dev/null; then
        log_info "Pre-restore backup saved to: $PRE_RESTORE_BACKUP"
    else
        log_warn "Failed to create pre-restore backup"
    fi
fi

# Start restore process
log_info "Starting database restore"

# Drop and recreate database
log_info "Dropping existing database"
PGPASSWORD="${DB_PASSWORD:-}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" || {
        log_error "Failed to drop database"
        exit 1
    }

log_info "Creating new database"
PGPASSWORD="${DB_PASSWORD:-}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || {
        log_error "Failed to create database"
        exit 1
    }

# Restore from backup
log_info "Restoring database from backup"
if gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD:-}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --single-transaction \
    -v ON_ERROR_STOP=1; then
    
    log_info "Database restore completed successfully"
    
    # Run post-restore checks
    log_info "Running post-restore checks"
    
    # Check table count
    TABLE_COUNT=$(PGPASSWORD="${DB_PASSWORD:-}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    log_info "Restored tables: $TABLE_COUNT"
    
    # Check key tables
    for table in users organizations products; do
        if PGPASSWORD="${DB_PASSWORD:-}" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -c "SELECT COUNT(*) FROM $table;" &>/dev/null; then
            COUNT=$(PGPASSWORD="${DB_PASSWORD:-}" psql \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                -t -c "SELECT COUNT(*) FROM $table;")
            log_info "Table '$table' has $COUNT records"
        fi
    done
    
else
    log_error "Database restore failed"
    
    # Attempt to restore pre-restore backup
    if [ -f "${PRE_RESTORE_BACKUP:-}" ]; then
        log_warn "Attempting to restore pre-restore backup"
        gunzip -c "$PRE_RESTORE_BACKUP" | PGPASSWORD="${DB_PASSWORD:-}" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" || log_error "Failed to restore pre-restore backup"
    fi
    
    exit 1
fi

# Clean up pre-restore backup if force mode
if [ "$FORCE" = true ] && [ -f "${PRE_RESTORE_BACKUP:-}" ]; then
    rm -f "$PRE_RESTORE_BACKUP"
fi

log_info "Database restore process completed"