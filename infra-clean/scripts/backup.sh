#!/bin/bash
# ITDO ERP v2 - Clean Production Backup Script
# CC03 v60.0 - Clean Production Implementation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="../compose/docker-compose.production.yml"
ENV_FILE="../compose/.env.production.secure"
BACKUP_DIR="/opt/itdo-erp/backups"
RETENTION_DAYS=30

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

# Create backup directory
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"/{database,redis,logs}
    chmod 700 "$BACKUP_DIR"
}

# Database backup
backup_database() {
    log "Starting database backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/database/postgres_backup_$timestamp.sql"
    
    if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U itdo_user >/dev/null 2>&1; then
        error "Database is not ready"
        return 1
    fi
    
    # Create database dump
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
        pg_dump -U itdo_user -d itdo_erp_prod --verbose > "$backup_file" 2>/dev/null
    
    # Compress backup
    gzip "$backup_file"
    
    log "Database backup completed: $backup_file.gz"
    
    # Verify backup
    if [[ -f "$backup_file.gz" ]] && [[ $(stat -c%s "$backup_file.gz") -gt 1000 ]]; then
        log "Database backup verified successfully"
    else
        error "Database backup verification failed"
        return 1
    fi
}

# Redis backup
backup_redis() {
    log "Starting Redis backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/redis/redis_backup_$timestamp.rdb"
    
    # Trigger Redis BGSAVE
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli --raw LASTSAVE > /tmp/lastsave_before 2>/dev/null
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli --raw BGSAVE >/dev/null 2>&1
    
    # Wait for backup to complete
    local attempts=0
    local max_attempts=30
    while [[ $attempts -lt $max_attempts ]]; do
        local current_save=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli --raw LASTSAVE)
        local previous_save=$(cat /tmp/lastsave_before 2>/dev/null || echo "0")
        
        if [[ "$current_save" != "$previous_save" ]]; then
            break
        fi
        
        sleep 2
        ((attempts++))
    done
    
    if [[ $attempts -eq $max_attempts ]]; then
        warn "Redis backup may not have completed in time"
    fi
    
    # Copy Redis dump
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis cat /data/dump.rdb > "$backup_file"
    
    # Compress backup
    gzip "$backup_file"
    
    log "Redis backup completed: $backup_file.gz"
    
    # Cleanup temp file
    rm -f /tmp/lastsave_before
}

# Log backup
backup_logs() {
    log "Starting log backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local log_backup_dir="$BACKUP_DIR/logs/logs_$timestamp"
    
    mkdir -p "$log_backup_dir"
    
    # Copy container logs
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs --no-color > "$log_backup_dir/container_logs.txt" 2>/dev/null || warn "Failed to backup container logs"
    
    # Copy NGINX logs if accessible
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T nginx sh -c "tar -czf - /var/log/nginx/" > "$log_backup_dir/nginx_logs.tar.gz" 2>/dev/null || warn "Failed to backup NGINX logs"
    
    # Compress log directory
    tar -czf "$log_backup_dir.tar.gz" -C "$BACKUP_DIR/logs" "logs_$timestamp"
    rm -rf "$log_backup_dir"
    
    log "Log backup completed: $log_backup_dir.tar.gz"
}

# Full backup
backup_all() {
    log "Starting full backup..."
    
    setup_backup_dir
    
    backup_database
    backup_redis
    backup_logs
    
    # Create manifest
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local manifest_file="$BACKUP_DIR/backup_manifest_$timestamp.txt"
    
    cat > "$manifest_file" << EOF
ITDO ERP v2 - Backup Manifest
Timestamp: $(date)
Version: CC03 v60.0

Files:
$(find "$BACKUP_DIR" -name "*$timestamp*" -type f | sort)

Sizes:
$(find "$BACKUP_DIR" -name "*$timestamp*" -type f -exec ls -lh {} \; | awk '{print $5, $9}')
EOF
    
    log "Full backup completed successfully"
    log "Manifest: $manifest_file"
}

# List backups
list_backups() {
    log "Available backups:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "No backup directory found"
        return
    fi
    
    echo ""
    echo "Database backups:"
    find "$BACKUP_DIR/database" -name "*.sql.gz" -type f 2>/dev/null | sort -r | head -10 || echo "  No database backups found"
    
    echo ""
    echo "Redis backups:"
    find "$BACKUP_DIR/redis" -name "*.rdb.gz" -type f 2>/dev/null | sort -r | head -10 || echo "  No Redis backups found"
    
    echo ""
    echo "Log backups:"
    find "$BACKUP_DIR/logs" -name "*.tar.gz" -type f 2>/dev/null | sort -r | head -10 || echo "  No log backups found"
    
    echo ""
    echo "Backup manifests:"
    find "$BACKUP_DIR" -name "backup_manifest_*.txt" -type f 2>/dev/null | sort -r | head -10 || echo "  No manifests found"
}

# Restore database
restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        error "Please specify backup file"
        list_recent_backups "database"
        return 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    log "Restoring database from: $backup_file"
    
    warn "This will overwrite the current database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Restore cancelled"
        return 0
    fi
    
    # Stop backend to prevent connections
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop backend frontend
    
    # Restore database
    if [[ "$backup_file" == *.gz ]]; then
        zcat "$backup_file" | docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U itdo_user -d itdo_erp_prod
    else
        cat "$backup_file" | docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U itdo_user -d itdo_erp_prod
    fi
    
    # Restart services
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" start backend frontend
    
    log "Database restore completed"
}

# List recent backups by type
list_recent_backups() {
    local type="$1"
    echo "Recent $type backups:"
    find "$BACKUP_DIR/$type" -name "*.gz" -type f 2>/dev/null | sort -r | head -5 | while read -r backup; do
        echo "  $(basename "$backup") - $(date -r "$backup" '+%Y-%m-%d %H:%M:%S')"
    done
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "No backup directory found"
        return
    fi
    
    local deleted_count=0
    
    # Cleanup database backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR/database" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null || true)
    
    # Cleanup Redis backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR/redis" -name "*.rdb.gz" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null || true)
    
    # Cleanup log backups
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR/logs" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null || true)
    
    # Cleanup manifests
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "backup_manifest_*.txt" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null || true)
    
    log "Deleted $deleted_count old backup files"
}

# Show usage
usage() {
    echo "Usage: $0 {backup|restore|list|cleanup}"
    echo ""
    echo "Commands:"
    echo "  backup              - Create full backup (database + redis + logs)"
    echo "  restore <file>      - Restore database from backup file"
    echo "  list                - List available backups"
    echo "  cleanup             - Remove backups older than $RETENTION_DAYS days"
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        "backup")
            backup_all
            ;;
        "restore")
            restore_database "${2:-}"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"