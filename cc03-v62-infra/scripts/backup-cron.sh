#!/bin/bash
# CC03 v62.0 - バックアップCronスクリプト

set -euo pipefail

# 環境変数確認
: "${POSTGRES_DB:?}"
: "${POSTGRES_USER:?}"
: "${POSTGRES_PASSWORD:?}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# データベースバックアップ実行
backup_database() {
    local backup_file="/backup/postgres_$(date +%Y%m%d_%H%M%S).sql"
    
    log "データベースバックアップ開始: $backup_file"
    
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h postgres \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        > "$backup_file"
    
    # 圧縮
    gzip "$backup_file"
    
    log "データベースバックアップ完了: $backup_file.gz"
}

# 古いバックアップ削除
cleanup_old_backups() {
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    
    log "古いバックアップを削除中 (${retention_days}日以上前)"
    
    find /backup -name "postgres_*.sql.gz" -mtime +${retention_days} -delete
    
    log "古いバックアップ削除完了"
}

# メイン処理
main() {
    log "バックアップ処理開始"
    
    # バックアップディレクトリ作成
    mkdir -p /backup
    
    # PostgreSQL接続待機
    while ! PGPASSWORD="$POSTGRES_PASSWORD" pg_isready -h postgres -U "$POSTGRES_USER"; do
        log "PostgreSQL接続待機中..."
        sleep 10
    done
    
    # バックアップ実行
    backup_database
    cleanup_old_backups
    
    log "バックアップ処理完了"
    
    # 24時間待機してから再実行
    sleep 86400
    exec "$0"
}

main "$@"