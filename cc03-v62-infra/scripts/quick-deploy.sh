#!/bin/bash
# CC03 v62.0 - 7日間集中インフラスプリント
# Day 1: クイックデプロイスクリプト

set -euo pipefail

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

# 前提条件チェック
check_prerequisites() {
    log "前提条件をチェック中..."
    
    if ! command -v podman >/dev/null 2>&1; then
        error "Podmanがインストールされていません"
        exit 1
    fi
    
    if ! podman info >/dev/null 2>&1; then
        error "Podmanが実行されていません"
        exit 1
    fi
    
    if ! command -v podman-compose >/dev/null 2>&1; then
        error "Podman Composeがインストールされていません"
        exit 1
    fi
    
    # 必要なファイルの存在確認
    local required_files=(
        "docker-compose.production.yml"
        ".env.production"
        "config/nginx.conf"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "必要なファイルが見つかりません: $file"
            exit 1
        fi
    done
    
    log "前提条件チェック完了"
}

# SSL証明書セットアップ
setup_ssl() {
    log "SSL証明書をセットアップ中..."
    
    local ssl_dir="config/ssl"
    mkdir -p "$ssl_dir"
    
    if [[ ! -f "$ssl_dir/cert.pem" ]] || [[ ! -f "$ssl_dir/key.pem" ]]; then
        info "開発用自己署名証明書を生成中..."
        
        # 秘密鍵生成
        openssl genrsa -out "$ssl_dir/key.pem" 2048
        
        # 証明書生成（複数サブドメイン対応）
        openssl req -new -x509 -key "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 \
            -subj "/C=JP/ST=Tokyo/L=Tokyo/O=ITDO/CN=itdo-erp-v62.com" \
            -addext "subjectAltName=DNS:itdo-erp-v62.com,DNS:www.itdo-erp-v62.com,DNS:api.itdo-erp-v62.com,DNS:auth.itdo-erp-v62.com,DNS:monitor.itdo-erp-v62.com"
        
        # 権限設定
        chmod 600 "$ssl_dir/key.pem"
        chmod 644 "$ssl_dir/cert.pem"
        
        log "SSL証明書生成完了"
    else
        log "SSL証明書は既に存在します"
    fi
}

# Docker Composeファイル検証
validate_compose() {
    log "Docker Compose設定を検証中..."
    
    if podman-compose -f docker-compose.production.yml --env-file .env.production config >/dev/null 2>&1; then
        log "Podman Compose設定は有効です"
    else
        error "Podman Compose設定に問題があります"
        podman-compose -f docker-compose.production.yml --env-file .env.production config
        exit 1
    fi
}

# サービスデプロイ
deploy_services() {
    log "サービスをデプロイ中..."
    
    # 既存のサービス停止
    info "既存サービスを停止中..."
    podman-compose -f docker-compose.production.yml --env-file .env.production down --remove-orphans || true
    
    # 最新イメージプル
    info "最新イメージを取得中..."
    podman-compose -f docker-compose.production.yml --env-file .env.production pull || warn "一部イメージの取得に失敗"
    
    # サービス起動
    info "サービスを起動中..."
    podman-compose -f docker-compose.production.yml --env-file .env.production up -d
    
    log "サービスデプロイ完了"
}

# ヘルスチェック
health_check() {
    log "ヘルスチェックを実行中..."
    
    local services=(
        "postgres:PostgreSQL"
        "redis:Redis"
        "backend:Backend API"
        "frontend:Frontend"
        "nginx:NGINX"
        "keycloak:Keycloak"
        "prometheus:Prometheus"
        "grafana:Grafana"
    )
    
    info "サービス起動を待機中..."
    sleep 30
    
    local all_healthy=true
    
    for service_info in "${services[@]}"; do
        local service_name="${service_info%%:*}"
        local service_desc="${service_info##*:}"
        
        if podman-compose -f docker-compose.production.yml --env-file .env.production ps "$service_name" | grep -q "Up"; then
            echo -e "  ${GREEN}✓${NC} $service_desc"
        else
            echo -e "  ${RED}✗${NC} $service_desc - 起動に失敗"
            all_healthy=false
        fi
    done
    
    if $all_healthy; then
        log "全サービスが正常に起動しました"
    else
        error "一部サービスの起動に問題があります"
        return 1
    fi
}

# 接続テスト
connectivity_test() {
    log "接続テストを実行中..."
    
    local tests=(
        "https://localhost/health:フロントエンド"
        "https://localhost/api/v1/health:API"
    )
    
    info "接続テストを開始..."
    sleep 10
    
    for test_info in "${tests[@]}"; do
        local url="${test_info%%:*}"
        local desc="${test_info ##*:}"
        
        if curl -k -s -f "$url" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $desc 接続OK"
        else
            echo -e "  ${YELLOW}⚠${NC} $desc 接続待機中..."
        fi
    done
    
    log "接続テスト完了"
}

# ステータス表示
show_status() {
    log "デプロイ状況サマリー"
    
    echo ""
    info "アクセスURL:"
    echo "  メインアプリ: https://localhost"
    echo "  API:         https://localhost/api/v1/"
    echo "  監視:        https://localhost:3001 (Grafana)"
    echo "  メトリクス:   http://localhost:9090 (Prometheus)"
    echo "  アラート:     http://localhost:9093 (Alertmanager)"
    
    echo ""
    info "コンテナ状況:"
    podman-compose -f docker-compose.production.yml --env-file .env.production ps
    
    echo ""
    info "リソース使用状況:"
    podman stats --no-stream --format "table {{.Names}}\t{{.CPU%}}\t{{.MemUsage}}\t{{.Mem%}}"
}

# メイン実行
main() {
    log "=== CC03 v62.0 Day 1: クイックデプロイ開始 ==="
    
    check_prerequisites
    setup_ssl
    validate_compose
    deploy_services
    health_check
    connectivity_test
    show_status
    
    log "=== Day 1: デプロイ完了 ==="
    warn "注意: 開発用自己署名証明書を使用しています"
    warn "本番環境では適切なSSL証明書に置き換えてください"
}

# エラーハンドリング
trap 'error "スクリプト実行中にエラーが発生しました (行: $LINENO)"' ERR

# 実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi