#!/bin/bash
# ITDO ERP v2 - 45日間安定インフラ 監視スクリプト
# CC03 v61.0 - シンプル監視

set -euo pipefail

# 色設定
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO: $1${NC}"
}

# サービスヘルスチェック
check_services() {
    log "サービスヘルスチェック実行中..."
    
    local services=("postgres" "redis" "backend" "frontend" "nginx" "monitor")
    local all_healthy=true
    
    echo ""
    for service in "${services[@]}"; do
        if docker compose ps "$service" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} $service - 正常"
        else
            echo -e "  ${RED}✗${NC} $service - 異常"
            all_healthy=false
        fi
    done
    
    echo ""
    if $all_healthy; then
        log "全サービス正常動作中"
    else
        error "一部サービスに問題があります"
    fi
}

# リソース使用状況確認
check_resources() {
    log "リソース使用状況確認中..."
    
    echo ""
    info "CPU・メモリ使用状況:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo ""
    info "ディスク使用状況:"
    df -h / | grep -v Filesystem
    
    echo ""
    info "Dockerボリューム使用状況:"
    docker system df
}

# 接続テスト
test_connectivity() {
    log "接続テスト実行中..."
    
    echo ""
    
    # フロントエンド接続テスト
    if curl -s -k https://localhost/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} フロントエンド接続OK"
    else
        echo -e "  ${RED}✗${NC} フロントエンド接続エラー"
    fi
    
    # API接続テスト
    if curl -s -k https://localhost/api/v1/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} API接続OK"
    else
        echo -e "  ${RED}✗${NC} API接続エラー"
    fi
    
    # データベース接続テスト
    if docker compose exec -T postgres pg_isready -U itdo_user >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} データベース接続OK"
    else
        echo -e "  ${RED}✗${NC} データベース接続エラー"
    fi
    
    # Redis接続テスト
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Redis接続OK"
    else
        echo -e "  ${RED}✗${NC} Redis接続エラー"
    fi
    
    # 監視システム接続テスト
    if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} 監視システム接続OK"
    else
        echo -e "  ${RED}✗${NC} 監視システム接続エラー"
    fi
}

# ログ確認
check_logs() {
    log "最近のエラーログを確認中..."
    
    echo ""
    info "NGINX エラーログ:"
    docker compose logs nginx --tail 5 2>/dev/null | grep -i error || echo "  エラーなし"
    
    echo ""
    info "Backend エラーログ:"
    docker compose logs backend --tail 5 2>/dev/null | grep -i error || echo "  エラーなし"
    
    echo ""
    info "PostgreSQL ログ:"
    docker compose logs postgres --tail 5 2>/dev/null | grep -i error || echo "  エラーなし"
}

# パフォーマンス情報表示
show_performance() {
    log "パフォーマンス情報表示中..."
    
    echo ""
    info "レスポンス時間測定:"
    
    # フロントエンドレスポンス時間
    local frontend_time=$(curl -s -k -w "%{time_total}" -o /dev/null https://localhost/health 2>/dev/null || echo "0")
    echo "  フロントエンド: ${frontend_time}秒"
    
    # APIレスポンス時間
    local api_time=$(curl -s -k -w "%{time_total}" -o /dev/null https://localhost/api/v1/health 2>/dev/null || echo "0")
    echo "  API: ${api_time}秒"
    
    echo ""
    info "データベース統計:"
    docker compose exec -T postgres psql -U itdo_user -d itdo_erp_stable -c "SELECT count(*) as connections FROM pg_stat_activity;" 2>/dev/null || echo "  取得失敗"
}

# 全体監視実行
monitor_all() {
    log "=== 45日間安定インフラ 監視レポート ==="
    log "実行時刻: $(date)"
    
    check_services
    echo ""
    check_resources
    echo ""
    test_connectivity
    echo ""
    check_logs
    echo ""
    show_performance
    
    echo ""
    log "=== 監視レポート終了 ==="
}

# 継続監視モード
watch_mode() {
    log "継続監視モード開始（Ctrl+Cで終了）"
    
    while true; do
        clear
        monitor_all
        sleep 30
    done
}

# 使用方法
usage() {
    echo "使用方法: $0 {all|services|resources|connectivity|logs|performance|watch}"
    echo ""
    echo "コマンド:"
    echo "  all           - 全監視項目を実行"
    echo "  services      - サービス状態確認"
    echo "  resources     - リソース使用状況確認"
    echo "  connectivity  - 接続テスト"
    echo "  logs          - エラーログ確認"
    echo "  performance   - パフォーマンス情報表示"
    echo "  watch         - 継続監視モード"
}

# メイン処理
main() {
    local command="${1:-all}"
    
    case "$command" in
        "all")
            monitor_all
            ;;
        "services")
            check_services
            ;;
        "resources")
            check_resources
            ;;
        "connectivity")
            test_connectivity
            ;;
        "logs")
            check_logs
            ;;
        "performance")
            show_performance
            ;;
        "watch")
            watch_mode
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"