#!/bin/bash
# ITDO ERP v2 - 45日間安定インフラ デプロイスクリプト
# CC03 v61.0 - シンプル運用

set -euo pipefail

# 色設定
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
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

# 前提条件チェック
check_prerequisites() {
    log "前提条件をチェック中..."
    
    if ! docker info >/dev/null 2>&1; then
        error "Dockerが実行されていません"
        exit 1
    fi
    
    if [[ ! -f "docker-compose.yml" ]]; then
        error "docker-compose.ymlが見つかりません"
        exit 1
    fi
    
    if [[ ! -f ".env" ]]; then
        error ".envファイルが見つかりません"
        exit 1
    fi
    
    log "前提条件OK"
}

# SSL証明書生成（開発用）
setup_ssl() {
    log "SSL証明書をセットアップ中..."
    
    mkdir -p ssl
    
    if [[ ! -f "ssl/cert.pem" ]] || [[ ! -f "ssl/key.pem" ]]; then
        log "開発用SSL証明書を生成中..."
        
        openssl req -x509 -newkey rsa:2048 -keyout ssl/key.pem -out ssl/cert.pem \
            -days 365 -nodes -subj "/CN=itdo-erp.local"
        
        chmod 600 ssl/key.pem
        chmod 644 ssl/cert.pem
        
        log "SSL証明書生成完了"
    else
        log "SSL証明書は既に存在します"
    fi
}

# デプロイ実行
deploy() {
    log "45日間安定インフラをデプロイ中..."
    
    # イメージプル
    log "最新イメージを取得中..."
    docker compose pull || warn "一部イメージの取得に失敗しました"
    
    # サービス停止
    log "既存サービスを停止中..."
    docker compose down
    
    # サービス開始
    log "サービスを開始中..."
    docker compose up -d
    
    # ヘルスチェック
    log "ヘルスチェック実行中..."
    sleep 10
    
    local services=("postgres" "redis" "backend" "frontend" "nginx")
    for service in "${services[@]}"; do
        if docker compose ps "$service" | grep -q "Up"; then
            log "✓ $service は正常です"
        else
            error "✗ $service に問題があります"
        fi
    done
    
    log "デプロイ完了"
    log "アクセスURL: https://itdo-erp.local"
    log "監視URL: https://monitor.itdo-erp.local:9090"
}

# ステータス確認
status() {
    log "サービス状態を確認中..."
    
    echo ""
    log "コンテナ状態:"
    docker compose ps
    
    echo ""
    log "ヘルスチェック:"
    local services=("postgres" "redis" "backend" "frontend" "nginx" "monitor")
    for service in "${services[@]}"; do
        if docker compose ps "$service" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} $service"
        else
            echo -e "  ${RED}✗${NC} $service"
        fi
    done
}

# ログ表示
logs() {
    local service="${1:-}"
    
    if [[ -n "$service" ]]; then
        log "$service のログを表示中..."
        docker compose logs -f "$service"
    else
        log "全サービスのログを表示中..."
        docker compose logs -f
    fi
}

# 停止
stop() {
    log "サービスを停止中..."
    docker compose down
    log "停止完了"
}

# 使用方法
usage() {
    echo "使用方法: $0 {deploy|status|logs|stop}"
    echo ""
    echo "コマンド:"
    echo "  deploy  - サービスをデプロイ"
    echo "  status  - サービス状態を確認"
    echo "  logs    - ログを表示"
    echo "  stop    - サービスを停止"
}

# メイン処理
main() {
    local command="${1:-}"
    
    case "$command" in
        "deploy")
            check_prerequisites
            setup_ssl
            deploy
            ;;
        "status")
            status
            ;;
        "logs")
            logs "${2:-}"
            ;;
        "stop")
            stop
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"