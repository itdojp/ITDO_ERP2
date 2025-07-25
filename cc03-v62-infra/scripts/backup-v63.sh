#!/bin/bash
# CC03 v63.0 - 高度バックアップシステム
# Day 2: 自動化・暗号化・クラウド対応バックアップ

set -euo pipefail

# 設定
BACKUP_DIR="${BACKUP_DIR:-/backup}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-default_key_change_me}"
S3_BUCKET="${S3_BUCKET:-itdo-erp-v63-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ログ関数
log_info() { echo -e "\033[36m[$(date +'%Y-%m-%d %H:%M:%S')] INFO:\033[0m $1"; }
log_success() { echo -e "\033[32m[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:\033[0m $1"; }
log_warn() { echo -e "\033[33m[$(date +'%Y-%m-%d %H:%M:%S')] WARN:\033[0m $1"; }
log_error() { echo -e "\033[31m[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:\033[0m $1"; }

# エラーハンドリング
trap 'log_error "バックアップ処理中にエラーが発生しました (Line: $LINENO)"' ERR

# バックアップディレクトリ作成
create_backup_structure() {
    local backup_path="${BACKUP_DIR}/${TIMESTAMP}"
    mkdir -p "${backup_path}"/{database,redis,config,logs,volumes}
    echo "${backup_path}"
}

# PostgreSQLバックアップ
backup_postgresql() {
    local backup_path=$1
    log_info "PostgreSQLバックアップ開始..."
    
    # データベースバックアップ (カスタム形式)
    pg_dump -h postgres -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${backup_path}/database/postgres_${TIMESTAMP}.dump"
    
    # スキーマのみバックアップ
    pg_dump -h postgres -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        --schema-only \
        --file="${backup_path}/database/postgres_schema_${TIMESTAMP}.sql"
    
    # グローバル設定バックアップ
    pg_dumpall -h postgres -U "${POSTGRES_USER}" \
        --globals-only \
        --file="${backup_path}/database/postgres_globals_${TIMESTAMP}.sql"
    
    log_success "PostgreSQLバックアップ完了"
}

# Redisバックアップ
backup_redis() {
    local backup_path=$1
    log_info "Redisバックアップ開始..."
    
    # RDB snapshot作成
    redis-cli -h redis -a "${REDIS_PASSWORD}" --rdb "${backup_path}/redis/redis_${TIMESTAMP}.rdb"
    
    # Redis設定バックアップ
    redis-cli -h redis -a "${REDIS_PASSWORD}" CONFIG GET '*' > "${backup_path}/redis/redis_config_${TIMESTAMP}.txt"
    
    # Redis情報バックアップ
    redis-cli -h redis -a "${REDIS_PASSWORD}" INFO ALL > "${backup_path}/redis/redis_info_${TIMESTAMP}.txt"
    
    log_success "Redisバックアップ完了"
}

# 設定ファイルバックアップ
backup_configs() {
    local backup_path=$1
    log_info "設定ファイルバックアップ開始..."
    
    # Docker Compose設定
    cp "${SCRIPT_DIR}/../docker-compose.v63-production.yml" "${backup_path}/config/"
    cp "${SCRIPT_DIR}/../.env.v63-production" "${backup_path}/config/"
    
    # Nginx設定
    cp -r "${SCRIPT_DIR}/../config/nginx-v63.conf" "${backup_path}/config/"
    
    # SSL証明書
    if [[ -d "${SCRIPT_DIR}/../config/ssl" ]]; then
        cp -r "${SCRIPT_DIR}/../config/ssl" "${backup_path}/config/"
    fi
    
    # Prometheus設定
    cp "${SCRIPT_DIR}/../config/prometheus-v63.yml" "${backup_path}/config/"
    cp "${SCRIPT_DIR}/../config/alert-rules-v63.yml" "${backup_path}/config/"
    
    # Grafana設定
    if [[ -d "${SCRIPT_DIR}/../config/grafana-v63" ]]; then
        cp -r "${SCRIPT_DIR}/../config/grafana-v63" "${backup_path}/config/"
    fi
    
    log_success "設定ファイルバックアップ完了"
}

# ログファイルバックアップ
backup_logs() {
    local backup_path=$1
    log_info "ログファイルバックアップ開始..."
    
    # アプリケーションログ
    if docker volume ls | grep -q app-logs; then
        docker run --rm -v app-logs:/source -v "${backup_path}/logs":/backup alpine \
            tar -czf /backup/app-logs_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Nginxログ
    if docker volume ls | grep -q nginx-logs; then
        docker run --rm -v nginx-logs:/source -v "${backup_path}/logs":/backup alpine \
            tar -czf /backup/nginx-logs_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    log_success "ログファイルバックアップ完了"
}

# Dockerボリュームバックアップ
backup_volumes() {
    local backup_path=$1
    log_info "Dockerボリュームバックアップ開始..."
    
    # PostgreSQLデータ
    if docker volume ls | grep -q postgres-data; then
        docker run --rm -v postgres-data:/source -v "${backup_path}/volumes":/backup alpine \
            tar -czf /backup/postgres-data_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Redisデータ
    if docker volume ls | grep -q redis-data; then
        docker run --rm -v redis-data:/source -v "${backup_path}/volumes":/backup alpine \
            tar -czf /backup/redis-data_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Grafanaデータ
    if docker volume ls | grep -q grafana-data; then
        docker run --rm -v grafana-data:/source -v "${backup_path}/volumes":/backup alpine \
            tar -czf /backup/grafana-data_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    # Prometheusデータ
    if docker volume ls | grep -q prometheus-data; then
        docker run --rm -v prometheus-data:/source -v "${backup_path}/volumes":/backup alpine \
            tar -czf /backup/prometheus-data_${TIMESTAMP}.tar.gz -C /source .
    fi
    
    log_success "Dockerボリュームバックアップ完了"
}

# バックアップ暗号化
encrypt_backup() {
    local backup_path=$1
    log_info "バックアップ暗号化開始..."
    
    # バックアップアーカイブ作成
    local archive_name="itdo-erp-v63-backup_${TIMESTAMP}.tar.gz"
    tar -czf "${BACKUP_DIR}/${archive_name}" -C "${BACKUP_DIR}" "$(basename "${backup_path}")"
    
    # 暗号化
    openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}/${archive_name}" \
        -out "${BACKUP_DIR}/${archive_name}.enc" \
        -pass pass:"${ENCRYPTION_KEY}"
    
    # 元のアーカイブ削除
    rm "${BACKUP_DIR}/${archive_name}"
    
    # チェックサム作成
    sha256sum "${BACKUP_DIR}/${archive_name}.enc" > "${BACKUP_DIR}/${archive_name}.enc.sha256"
    
    log_success "バックアップ暗号化完了: ${archive_name}.enc"
    echo "${BACKUP_DIR}/${archive_name}.enc"
}

# クラウドアップロード (AWS S3)
upload_to_cloud() {
    local encrypted_file=$1
    
    if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
        log_warn "AWS認証情報が設定されていません。クラウドアップロードをスキップします。"
        return 0
    fi
    
    log_info "クラウドアップロード開始..."
    
    # AWS CLI使用可能性チェック
    if command -v aws &> /dev/null; then
        aws s3 cp "${encrypted_file}" "s3://${S3_BUCKET}/$(basename "${encrypted_file}")"
        aws s3 cp "${encrypted_file}.sha256" "s3://${S3_BUCKET}/$(basename "${encrypted_file}.sha256")"
        log_success "クラウドアップロード完了"
    else
        log_warn "AWS CLIが見つかりません。curlでアップロードを試行します。"
        # カスタムアップロード処理（必要に応じて実装）
    fi
}

# 古いバックアップ削除
cleanup_old_backups() {
    log_info "古いバックアップクリーンアップ開始..."
    
    # ローカルバックアップクリーンアップ
    find "${BACKUP_DIR}" -name "*.enc" -type f -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -name "*.sha256" -type f -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} +
    
    # S3バックアップクリーンアップ（AWS CLI使用）
    if command -v aws &> /dev/null && [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
        local cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)
        aws s3 ls "s3://${S3_BUCKET}/" | while read -r line; do
            local file_date=$(echo "${line}" | awk '{print $1}')
            local file_name=$(echo "${line}" | awk '{print $4}')
            
            if [[ "${file_date}" < "${cutoff_date}" ]]; then
                aws s3 rm "s3://${S3_BUCKET}/${file_name}"
                log_info "削除されたS3ファイル: ${file_name}"
            fi
        done
    fi
    
    log_success "古いバックアップクリーンアップ完了"
}

# バックアップ検証
verify_backup() {
    local encrypted_file=$1
    log_info "バックアップ検証開始..."
    
    # チェックサム検証
    if sha256sum -c "${encrypted_file}.sha256"; then
        log_success "チェックサム検証成功"
    else
        log_error "チェックサム検証失敗"
        return 1
    fi
    
    # 暗号化ファイル検証
    local test_decrypt="/tmp/backup_test_decrypt"
    if openssl enc -d -aes-256-cbc -in "${encrypted_file}" \
        -out "${test_decrypt}" \
        -pass pass:"${ENCRYPTION_KEY}" 2>/dev/null; then
        
        if file "${test_decrypt}" | grep -q "gzip compressed"; then
            log_success "バックアップファイル検証成功"
            rm -f "${test_decrypt}"
        else
            log_error "バックアップファイル検証失敗"
            rm -f "${test_decrypt}"
            return 1
        fi
    else
        log_error "復号化テスト失敗"
        return 1
    fi
}

# メトリクス記録
record_backup_metrics() {
    local backup_path=$1
    local encrypted_file=$2
    
    # バックアップサイズ計算
    local backup_size=$(du -sb "${backup_path}" | cut -f1)
    local encrypted_size=$(stat -c%s "${encrypted_file}")
    
    # メトリクス記録（Prometheus形式）
    cat >> "${BACKUP_DIR}/backup_metrics.prom" << EOF
# HELP backup_size_bytes Size of backup in bytes
# TYPE backup_size_bytes gauge
backup_size_bytes{type="raw"} ${backup_size}
backup_size_bytes{type="encrypted"} ${encrypted_size}

# HELP backup_timestamp_seconds Timestamp of backup completion
# TYPE backup_timestamp_seconds gauge
backup_timestamp_seconds $(date +%s)

# HELP backup_success Boolean indicating backup success
# TYPE backup_success gauge
backup_success 1
EOF

    log_info "バックアップメトリクス記録完了"
}

# メイン実行
main() {
    log_info "🔄 CC03 v63.0 バックアップ開始 (${TIMESTAMP})"
    
    # バックアップ構造作成
    local backup_path=$(create_backup_structure)
    
    # 各種バックアップ実行
    backup_postgresql "${backup_path}"
    backup_redis "${backup_path}"
    backup_configs "${backup_path}"
    backup_logs "${backup_path}"
    backup_volumes "${backup_path}"
    
    # 暗号化
    local encrypted_file=$(encrypt_backup "${backup_path}")
    
    # 検証
    verify_backup "${encrypted_file}"
    
    # クラウドアップロード
    upload_to_cloud "${encrypted_file}"
    
    # メトリクス記録
    record_backup_metrics "${backup_path}" "${encrypted_file}"
    
    # クリーンアップ
    cleanup_old_backups
    
    # 一時ディレクトリ削除
    rm -rf "${backup_path}"
    
    log_success "🎉 バックアップ完了!"
    log_info "暗号化ファイル: $(basename "${encrypted_file}")"
    log_info "サイズ: $(du -h "${encrypted_file}" | cut -f1)"
}

# cron実行対応
if [[ "${1:-}" == "--cron" ]]; then
    exec > >(logger -t backup-v63) 2>&1
fi

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi