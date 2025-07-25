#!/bin/bash
# ITDO ERP v2 - 45日間安定インフラ バックアップスクリプト
# CC03 v61.0 - シンプル運用

set -euo pipefail

# 色設定
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# 設定
BACKUP_DIR="/opt/itdo-backups"
RETENTION_DAYS=7

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
}

# バックアップディレクトリ作成
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
}

# データベースバックアップ
backup_database() {
    log "データベースバックアップを実行中..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/postgres_$timestamp.sql"
    
    # データベース接続確認
    if ! docker compose exec -T postgres pg_isready -U itdo_user >/dev/null 2>&1; then
        error "データベースに接続できません"
        return 1
    fi
    
    # バックアップ実行
    docker compose exec -T postgres \
        pg_dump -U itdo_user -d itdo_erp_stable > "$backup_file"
    
    # 圧縮
    gzip "$backup_file"
    
    log "データベースバックアップ完了: $backup_file.gz"
}

# Redisバックアップ
backup_redis() {
    log "Redisバックアップを実行中..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/redis_$timestamp.rdb"
    
    # BGSAVE実行
    docker compose exec -T redis redis-cli --raw BGSAVE >/dev/null
    
    # しばらく待機
    sleep 5
    
    # ダンプファイルコピー
    docker compose exec -T redis cat /data/dump.rdb > "$backup_file"
    
    # 圧縮
    gzip "$backup_file"
    
    log "Redisバックアップ完了: $backup_file.gz"
}

# 全バックアップ実行
backup_all() {
    log "全バックアップを開始します..."
    
    setup_backup_dir
    backup_database
    backup_redis
    
    log "全バックアップ完了"
}

# バックアップ一覧表示
list_backups() {
    log "利用可能なバックアップ:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "バックアップディレクトリが見つかりません"
        return
    fi
    
    echo ""
    echo "データベースバックアップ:"
    find "$BACKUP_DIR" -name "postgres_*.sql.gz" -type f 2>/dev/null | sort -r | head -10 || echo "  バックアップなし"
    
    echo ""
    echo "Redisバックアップ:"
    find "$BACKUP_DIR" -name "redis_*.rdb.gz" -type f 2>/dev/null | sort -r | head -10 || echo "  バックアップなし"
}

# データベースリストア
restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        error "バックアップファイルを指定してください"
        list_recent_backups "postgres"
        return 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        error "バックアップファイルが見つかりません: $backup_file"
        return 1
    fi
    
    log "データベースリストア実行中: $backup_file"
    
    warn "現在のデータベースが上書きされます！"
    read -p "続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "リストアをキャンセルしました"
        return 0
    fi
    
    # バックエンド停止
    docker compose stop backend
    
    # リストア実行
    if [[ "$backup_file" == *.gz ]]; then
        zcat "$backup_file" | docker compose exec -T postgres psql -U itdo_user -d itdo_erp_stable
    else
        cat "$backup_file" | docker compose exec -T postgres psql -U itdo_user -d itdo_erp_stable
    fi
    
    # バックエンド開始
    docker compose start backend
    
    log "データベースリストア完了"
}

# 最近のバックアップ一覧
list_recent_backups() {
    local type="$1"
    echo "最近の$typeバックアップ:"
    find "$BACKUP_DIR" -name "$type_*.gz" -type f 2>/dev/null | sort -r | head -5 | while read -r backup; do
        echo "  $(basename "$backup") - $(date -r "$backup" '+%Y-%m-%d %H:%M:%S')"
    done
}

# 古いバックアップ削除
cleanup_old_backups() {
    log "${RETENTION_DAYS}日以上古いバックアップを削除中..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warn "バックアップディレクトリが見つかりません"
        return
    fi
    
    local deleted_count=0
    
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null || true)
    
    log "$deleted_count 個の古いファイルを削除しました"
}

# 使用方法
usage() {
    echo "使用方法: $0 {backup|restore|list|cleanup}"
    echo ""
    echo "コマンド:"
    echo "  backup              - 全バックアップ実行"
    echo "  restore <file>      - データベースリストア"
    echo "  list                - バックアップ一覧表示"
    echo "  cleanup             - 古いバックアップ削除"
}

# メイン処理
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

main "$@"