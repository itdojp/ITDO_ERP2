#!/bin/bash
# CC03 v63.0 - ゼロダウンタイムデプロイスクリプト
# Day 1: 本番グレード無停止デプロイ実装

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.v63-production.yml"
ENV_FILE="${PROJECT_DIR}/.env.v63-production"

# デプロイ設定
DEPLOYMENT_TIMEOUT=300
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10
ROLLBACK_ENABLED=true

# 色付きログ関数
log_info() { echo -e "\033[36m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warn() { echo -e "\033[33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# デプロイステップ表示
log_step() { echo -e "\033[35m[STEP $1]\033[0m $2"; }

# エラーハンドリング
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "エラーが発生しました (終了コード: $exit_code, 行: $line_number)"
    
    if [[ "${ROLLBACK_ENABLED}" == "true" ]]; then
        log_warn "ロールバックを実行します..."
        rollback_deployment
    fi
    
    exit $exit_code
}

# 前提条件チェック
check_prerequisites() {
    log_step "1" "前提条件チェック"
    
    # Docker/Podman確認
    if command -v podman &> /dev/null; then
        CONTAINER_CMD="podman"
        COMPOSE_CMD="podman-compose"
        log_info "Podman環境を検出"
    elif command -v docker &> /dev/null; then
        CONTAINER_CMD="docker"
        COMPOSE_CMD="docker-compose"
        log_info "Docker環境を検出"
    else
        log_error "DockerまたはPodmanが見つかりません"
        exit 1
    fi
    
    # Compose ファイル確認
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_error "Docker Compose ファイルが見つかりません: ${COMPOSE_FILE}"
        exit 1
    fi
    
    # 環境変数ファイル確認
    if [[ ! -f "${ENV_FILE}" ]]; then
        log_error "環境変数ファイルが見つかりません: ${ENV_FILE}"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 現在のサービス状態保存
backup_current_state() {
    log_step "2" "現在のサービス状態バックアップ"
    
    local backup_dir="${PROJECT_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${backup_dir}"
    
    # 現在のCompose設定をバックアップ
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config > "${backup_dir}/current-config.yml" 2>/dev/null; then
        log_info "Compose設定をバックアップ: ${backup_dir}/current-config.yml"
    fi
    
    # 現在のコンテナ状態をバックアップ
    ${CONTAINER_CMD} ps --format json > "${backup_dir}/containers-state.json" 2>/dev/null || true
    
    # データベースバックアップ
    if ${CONTAINER_CMD} ps --filter "name=itdo-postgres-v63" --filter "status=running" --quiet; then
        log_info "データベースバックアップ実行中..."
        ${CONTAINER_CMD} exec itdo-postgres-v63 pg_dump -U "${POSTGRES_USER:-itdo_admin}" -d "${POSTGRES_DB:-itdo_erp_v63}" > "${backup_dir}/database-backup.sql" 2>/dev/null || log_warn "データベースバックアップに失敗"
    fi
    
    echo "${backup_dir}" > "${PROJECT_DIR}/.last-backup"
    log_success "バックアップ完了: ${backup_dir}"
}

# イメージビルド（必要な場合）
build_images() {
    log_step "3" "アプリケーションイメージビルド"
    
    # フロントエンドイメージビルド
    if [[ -d "${PROJECT_DIR}/../frontend" ]]; then
        log_info "フロントエンドイメージビルド中..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build frontend
    else
        log_warn "フロントエンドソースディレクトリが見つかりません"
    fi
    
    # バックエンドイメージビルド
    if [[ -d "${PROJECT_DIR}/../backend" ]]; then
        log_info "バックエンドイメージビルド中..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build backend
    else
        log_warn "バックエンドソースディレクトリが見つかりません"
    fi
    
    log_success "イメージビルド完了"
}

# ヘルスチェック実行
health_check() {
    local service_name=$1
    local health_url=$2
    local retries=${3:-$HEALTH_CHECK_RETRIES}
    
    log_info "${service_name} ヘルスチェック開始..."
    
    for ((i=1; i<=retries; i++)); do
        if curl -f -s "${health_url}" > /dev/null 2>&1; then
            log_success "${service_name} ヘルスチェック成功 (${i}/${retries})"
            return 0
        fi
        
        if [[ $i -lt $retries ]]; then
            log_info "${service_name} ヘルスチェック待機中... (${i}/${retries})"
            sleep $HEALTH_CHECK_INTERVAL
        fi
    done
    
    log_error "${service_name} ヘルスチェック失敗"
    return 1
}

# ローリングデプロイ実行
rolling_deploy() {
    log_step "4" "ローリングデプロイ実行"
    
    # データ層サービス（DB、Redis）の更新
    log_info "データ層サービス更新中..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d postgres redis
    
    # データ層ヘルスチェック
    sleep 30
    if ! health_check "PostgreSQL" "localhost:5432" 10; then
        log_error "PostgreSQL ヘルスチェック失敗"
        return 1
    fi
    
    # アプリケーション層サービス更新
    log_info "アプリケーション層サービス更新中..."
    
    # バックエンド更新（ローリング）
    if ${CONTAINER_CMD} ps --filter "name=itdo-backend-v63" --quiet; then
        log_info "バックエンドサービス更新中..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --no-deps backend
        sleep 45
        if ! health_check "Backend API" "http://localhost:8000/api/v1/health" 15; then
            log_error "バックエンド ヘルスチェック失敗"
            return 1
        fi
    fi
    
    # フロントエンド更新
    if ${CONTAINER_CMD} ps --filter "name=itdo-frontend-v63" --quiet; then
        log_info "フロントエンドサービス更新中..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --no-deps frontend
        sleep 30
        if ! health_check "Frontend" "http://localhost:3000/health" 10; then
            log_error "フロントエンド ヘルスチェック失敗"
            return 1
        fi
    fi
    
    # リバースプロキシ更新
    log_info "リバースプロキシ更新中..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --no-deps nginx
    sleep 10
    if ! health_check "Nginx" "http://localhost/health" 5; then
        log_error "Nginx ヘルスチェック失敗"
        return 1
    fi
    
    log_success "ローリングデプロイ完了"
}

# 監視・運用サービス更新
update_monitoring_services() {
    log_step "5" "監視・運用サービス更新"
    
    # 監視サービス更新
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d prometheus grafana alertmanager cadvisor
    
    # 監視サービスヘルスチェック
    sleep 30
    health_check "Prometheus" "http://localhost:9090/-/healthy" 10 || log_warn "Prometheus ヘルスチェック失敗"
    health_check "Grafana" "http://localhost:3001/api/health" 15 || log_warn "Grafana ヘルスチェック失敗"
    
    # バックアップサービス更新
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d backup
    
    log_success "監視・運用サービス更新完了"
}

# デプロイ後検証
post_deploy_verification() {
    log_step "6" "デプロイ後検証"
    
    # 全サービス状態確認
    log_info "全サービス状態確認中..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps
    
    # エンドツーエンドテスト
    log_info "エンドツーエンドテスト実行中..."
    
    # API疎通確認
    if curl -f -s "http://localhost/health" > /dev/null; then
        log_success "メインサイト疎通確認 OK"
    else
        log_error "メインサイト疎通確認 NG"
        return 1
    fi
    
    # データベース接続確認
    if ${CONTAINER_CMD} exec itdo-postgres-v63 pg_isready -U "${POSTGRES_USER:-itdo_admin}" > /dev/null; then
        log_success "データベース接続確認 OK"
    else
        log_error "データベース接続確認 NG"
        return 1
    fi
    
    # Redis接続確認
    if ${CONTAINER_CMD} exec itdo-redis-v63 redis-cli ping | grep -q "PONG"; then
        log_success "Redis接続確認 OK"
    else
        log_error "Redis接続確認 NG"
        return 1
    fi
    
    log_success "デプロイ後検証完了"
}

# ロールバック実行
rollback_deployment() {
    log_warn "ロールバック実行中..."
    
    if [[ -f "${PROJECT_DIR}/.last-backup" ]]; then
        local backup_dir=$(cat "${PROJECT_DIR}/.last-backup")
        
        if [[ -f "${backup_dir}/current-config.yml" ]]; then
            log_info "前のバージョンに復元中..."
            ${COMPOSE_CMD} -f "${backup_dir}/current-config.yml" up -d
            sleep 30
            
            # ロールバック後のヘルスチェック
            if health_check "Rollback Health Check" "http://localhost/health" 10; then
                log_success "ロールバック完了"
            else
                log_error "ロールバック後のヘルスチェックに失敗"
            fi
        else
            log_error "バックアップファイルが見つかりません"
        fi
    else
        log_error "バックアップ情報が見つかりません"
    fi
}

# デプロイ情報記録
record_deployment() {
    log_step "7" "デプロイ情報記録"
    
    local deploy_info="${PROJECT_DIR}/deployments/$(date +%Y%m%d_%H%M%S).json"
    mkdir -p "${PROJECT_DIR}/deployments"
    
    cat > "${deploy_info}" << EOF
{
  "deployment_id": "v63-$(date +%Y%m%d_%H%M%S)",
  "timestamp": "$(date -Iseconds)",
  "version": "CC03 v63.0",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
  "services": {
    "nginx": "$(${CONTAINER_CMD} inspect itdo-nginx-v63 --format '{{.Config.Image}}' 2>/dev/null || echo 'unknown')",
    "frontend": "$(${CONTAINER_CMD} inspect itdo-frontend-v63 --format '{{.Config.Image}}' 2>/dev/null || echo 'unknown')",
    "backend": "$(${CONTAINER_CMD} inspect itdo-backend-v63 --format '{{.Config.Image}}' 2>/dev/null || echo 'unknown')",
    "postgres": "$(${CONTAINER_CMD} inspect itdo-postgres-v63 --format '{{.Config.Image}}' 2>/dev/null || echo 'unknown')",
    "redis": "$(${CONTAINER_CMD} inspect itdo-redis-v63 --format '{{.Config.Image}}' 2>/dev/null || echo 'unknown')"
  },
  "status": "success"
}
EOF
    
    log_success "デプロイ情報記録完了: ${deploy_info}"
}

# メイン実行フロー
main() {
    local start_time=$(date +%s)
    
    log_info "🚀 CC03 v63.0 ゼロダウンタイムデプロイ開始"
    log_info "タイムスタンプ: $(date -Iseconds)"
    
    check_prerequisites
    backup_current_state
    build_images
    rolling_deploy
    update_monitoring_services
    post_deploy_verification
    record_deployment
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "🎉 ゼロダウンタイムデプロイ完了!"
    log_info "デプロイ時間: ${duration}秒"
    log_info "サービス稼働状況:"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --services | while read service; do
        if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps "${service}" | grep -q "Up"; then
            log_success "  ✓ ${service}: 稼働中"
        else
            log_warn "  ✗ ${service}: 停止中"
        fi
    done
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi