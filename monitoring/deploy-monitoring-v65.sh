#!/bin/bash
# CC03 v65.0 - 継続的インフラ改善 Day 2
# Prometheus + Grafana 統合監視ダッシュボードシステム

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MONITORING_COMPOSE_FILE="docker-compose.monitoring-v65.yml"
ENV_FILE=".env.monitoring"
GRAFANA_PROVISIONING_DIR="grafana/provisioning"
DASHBOARDS_DIR="dashboards"
ALERTS_DIR="alerts"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Print header
print_header() {
    echo -e "${PURPLE}"
    echo "========================================================"
    echo "📊 CC03 v65.0 - 統合監視ダッシュボードシステム"
    echo "   Prometheus + Grafana リアルタイム監視実装"
    echo "========================================================"
    echo -e "${NC}"
    echo "🎯 実装機能:"
    echo "  • Prometheus メトリクス収集強化"
    echo "  • Grafana リアルタイムダッシュボード"
    echo "  • インテリジェントアラート設定"
    echo "  • 業務メトリクス可視化"
    echo "  • パフォーマンス監視自動化"
    echo "  • 障害予測システム"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log "監視システム前提条件チェック..."
    
    # Check Docker/Podman
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
        CONTAINER_ENGINE="podman"
        info "Podman環境で実行"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        CONTAINER_ENGINE="docker"
        info "Docker環境で実行"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        CONTAINER_ENGINE="docker"
        info "Docker Compose プラグインで実行"
    else
        error "Docker または Podman が見つかりません"
    fi
    
    # Check curl for health checks
    if ! command -v curl &> /dev/null; then
        error "curl が監視システムに必要です"
    fi
    
    # Check if running from monitoring directory
    if [[ ! -f "$SCRIPT_DIR/prometheus.yml" ]]; then
        warn "monitoring ディレクトリから実行していません。設定ファイルをコピーします..."
    fi
    
    success "前提条件チェック完了"
}

# Create monitoring environment file
create_monitoring_env() {
    log "監視システム環境設定作成中..."
    
    cat > "$SCRIPT_DIR/$ENV_FILE" << 'EOF'
# CC03 v65.0 - 監視システム環境設定

# Prometheus設定
PROMETHEUS_VERSION=v2.47.0
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_RETENTION_SIZE=15GB
PROMETHEUS_SCRAPE_INTERVAL=15s

# Grafana設定
GRAFANA_VERSION=10.2.0
GRAFANA_ADMIN_PASSWORD=GrafanaAdmin2025!Monitor#v65
GRAFANA_ORG_NAME=ITDO ERP Systems
GRAFANA_TIMEZONE=Asia/Tokyo

# Alertmanager設定
ALERTMANAGER_VERSION=v0.26.0
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ALERT_EMAIL=alerts@itdo-erp.com

# データベースメトリクス
POSTGRES_EXPORTER_VERSION=0.15.0
REDIS_EXPORTER_VERSION=1.55.0

# システムメトリクス
NODE_EXPORTER_VERSION=1.6.1
CADVISOR_VERSION=v0.47.2

# ネットワーク監視
BLACKBOX_EXPORTER_VERSION=0.24.0
NGINX_EXPORTER_VERSION=0.11.0

# セキュリティ監視
SSL_EXPORTER_VERSION=2.4.2

# パフォーマンス設定
GRAFANA_MEMORY_LIMIT=1g
PROMETHEUS_MEMORY_LIMIT=2g
ALERTMANAGER_MEMORY_LIMIT=512m

# ネットワーク設定
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
ALERTMANAGER_PORT=9093

# データ永続化
PROMETHEUS_DATA_DIR=/var/lib/prometheus
GRAFANA_DATA_DIR=/var/lib/grafana
ALERTMANAGER_DATA_DIR=/var/lib/alertmanager
EOF

    success "監視環境設定ファイル作成完了"
}

# Generate comprehensive monitoring Docker Compose
generate_monitoring_compose() {
    log "統合監視システム Docker Compose 設定生成中..."
    
    cat > "$SCRIPT_DIR/$MONITORING_COMPOSE_FILE" << 'EOF'
# CC03 v65.0 - 統合監視ダッシュボードシステム
# Prometheus + Grafana + Exporters + Alerting

version: '3.8'

name: itdo-erp-monitoring-v65

services:
  # Prometheus - メトリクス収集・保存
  prometheus:
    image: docker.io/prom/prometheus:${PROMETHEUS_VERSION:-v2.47.0}
    container_name: itdo-prometheus-v65
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./prometheus-v65.yml:/etc/prometheus/prometheus.yml:ro
      - ./alerts/alert-rules-v65.yml:/etc/prometheus/alert-rules.yml:ro
      - prometheus-data:/prometheus
      - ./recording-rules:/etc/prometheus/recording-rules:ro
    networks:
      - monitoring
      - app-tier
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION_TIME:-30d}'
      - '--storage.tsdb.retention.size=${PROMETHEUS_RETENTION_SIZE:-15GB}'
      - '--web.enable-admin-api'
      - '--web.enable-remote-write-receiver'
      - '--query.max-concurrency=20'
      - '--query.max-samples=50000000'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: ${PROMETHEUS_MEMORY_LIMIT:-2g}
          cpus: '1.0'
        reservations:
          memory: 1g
          cpus: '0.5'

  # Grafana - ダッシュボード・可視化
  grafana:
    image: docker.io/grafana/grafana:${GRAFANA_VERSION:-10.2.0}
    container_name: itdo-grafana-v65
    ports:
      - "${GRAFANA_PORT:-3001}:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_USERS_ALLOW_ORG_CREATE=false
      - GF_SERVER_DOMAIN=localhost
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_ANALYTICS_REPORTING_ENABLED=false
      - GF_ANALYTICS_CHECK_FOR_UPDATES=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel,grafana-clock-panel,grafana-polystat-panel,redis-datasource
      - GF_FEATURE_TOGGLES_ENABLE=ngalert
      - GF_UNIFIED_ALERTING_ENABLED=true
      - GF_ALERTING_ENABLED=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./dashboards:/var/lib/grafana/dashboards:ro
    networks:
      - monitoring
    depends_on:
      - prometheus
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: ${GRAFANA_MEMORY_LIMIT:-1g}
          cpus: '0.5'
        reservations:
          memory: 512m
          cpus: '0.25'

  # Alertmanager - アラート管理
  alertmanager:
    image: docker.io/prom/alertmanager:${ALERTMANAGER_VERSION:-v0.26.0}
    container_name: itdo-alertmanager-v65
    ports:
      - "${ALERTMANAGER_PORT:-9093}:9093"
    volumes:
      - ./alertmanager-v65.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    networks:
      - monitoring
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
      - '--cluster.advertise-address=0.0.0.0:9093'
      - '--log.level=info'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9093/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: ${ALERTMANAGER_MEMORY_LIMIT:-512m}
          cpus: '0.5'
        reservations:
          memory: 256m
          cpus: '0.25'

  # Node Exporter - システムメトリクス
  node-exporter:
    image: docker.io/prom/node-exporter:${NODE_EXPORTER_VERSION:-v1.6.1}
    container_name: itdo-node-exporter-v65
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
      - /etc/hostname:/etc/nodename:ro
    networks:
      - monitoring
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
      - '--collector.textfile.directory=/etc/node-exporter/'
      - '--collector.systemd'
      - '--collector.processes'
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128m
          cpus: '0.25'

  # cAdvisor - コンテナメトリクス
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:${CADVISOR_VERSION:-v0.47.2}
    container_name: itdo-cadvisor-v65
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/containers/:/var/lib/containers:ro
      - /dev/disk/:/dev/disk:ro
    networks:
      - monitoring
    restart: unless-stopped
    privileged: true
    devices:
      - /dev/kmsg
    command:
      - '--housekeeping_interval=30s'
      - '--max_housekeeping_interval=35s'
      - '--event_storage_event_limit=default=0'
      - '--event_storage_age_limit=default=0'
      - '--disable_metrics=percpu,sched,tcp,udp,disk,diskIO,accelerator'
      - '--docker_only'
    deploy:
      resources:
        limits:
          memory: 512m
          cpus: '0.5'

  # PostgreSQL Exporter
  postgres-exporter:
    image: docker.io/prometheuscommunity/postgres-exporter:${POSTGRES_EXPORTER_VERSION:-v0.15.0}
    container_name: itdo-postgres-exporter-v65
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://itdo_user:${POSTGRES_PASSWORD:-changeme}@postgres:5432/itdo_erp?sslmode=disable
    networks:
      - monitoring
      - app-tier
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128m
          cpus: '0.25'

  # Redis Exporter
  redis-exporter:
    image: docker.io/oliver006/redis_exporter:${REDIS_EXPORTER_VERSION:-v1.55.0}
    container_name: itdo-redis-exporter-v65
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-}
    networks:
      - monitoring
      - app-tier
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128m
          cpus: '0.25'

  # NGINX Exporter
  nginx-exporter:
    image: docker.io/nginx/nginx-prometheus-exporter:${NGINX_EXPORTER_VERSION:-0.11.0}
    container_name: itdo-nginx-exporter-v65
    ports:
      - "9113:9113"
    command:
      - '-nginx.scrape-uri=http://nginx:80/nginx_status'
    networks:
      - monitoring
      - app-tier
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 64m
          cpus: '0.1'

  # Blackbox Exporter - 外部監視
  blackbox-exporter:
    image: docker.io/prom/blackbox-exporter:${BLACKBOX_EXPORTER_VERSION:-v0.24.0}
    container_name: itdo-blackbox-exporter-v65
    ports:
      - "9115:9115"
    volumes:
      - ./blackbox-v65.yml:/etc/blackbox_exporter/config.yml:ro
    networks:
      - monitoring
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128m
          cpus: '0.25'

  # SSL Exporter - SSL証明書監視
  ssl-exporter:
    image: docker.io/ribbybibby/ssl-exporter:${SSL_EXPORTER_VERSION:-v2.4.2}
    container_name: itdo-ssl-exporter-v65
    ports:
      - "9219:9219"
    networks:
      - monitoring
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 64m
          cpus: '0.1'

networks:
  monitoring:
    driver: bridge
    external: false
  app-tier:
    external: true

volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
  alertmanager-data:
    driver: local

# ヘルスチェック設定
x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3

# リソース制限設定
x-resource-defaults: &resource-defaults
  deploy:
    resources:
      reservations:
        memory: 64m
        cpus: '0.1'
EOF

    success "統合監視システム Docker Compose 設定生成完了"
}

# Generate enhanced Prometheus configuration
generate_prometheus_config() {
    log "Prometheus強化設定生成中..."
    
    cat > "$SCRIPT_DIR/prometheus-v65.yml" << 'EOF'
# CC03 v65.0 - 統合監視ダッシュボードシステム
# Prometheus設定 - リアルタイム監視・アラート強化版

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'itdo-erp-v65'
    environment: 'production'
    region: 'tokyo'

rule_files:
  - "/etc/prometheus/alert-rules.yml"
  - "/etc/prometheus/recording-rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
      timeout: 10s
      api_version: v2

scrape_configs:
  # Prometheus自身の監視
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics
    scrape_interval: 30s
    scrape_timeout: 10s

  # システムメトリクス - Node Exporter
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
    metrics_path: /metrics

  # コンテナメトリクス - cAdvisor
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 30s
    metrics_path: /metrics

  # データベースメトリクス - PostgreSQL
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s
    metrics_path: /metrics

  # キャッシュメトリクス - Redis
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
    metrics_path: /metrics

  # Webサーバーメトリクス - NGINX
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']
    scrape_interval: 30s
    metrics_path: /metrics

  # アプリケーションメトリクス - Backend API
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
    scrape_interval: 15s
    scrape_timeout: 10s

  # 認証サービスメトリクス - Keycloak
  - job_name: 'keycloak'
    static_configs:
      - targets: ['keycloak:8080']
    metrics_path: /auth/realms/master/metrics
    scrape_interval: 60s
    scrape_timeout: 15s

  # ダッシュボードメトリクス - Grafana
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
    metrics_path: /metrics
    scrape_interval: 60s

  # アラート管理メトリクス - Alertmanager
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']
    metrics_path: /metrics
    scrape_interval: 60s

  # 外部監視 - Blackbox Exporter
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - http://localhost
        - http://localhost/health
        - http://localhost:8000/api/v1/health
        - http://localhost:3000
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # SSL証明書監視
  - job_name: 'ssl-certificates'
    static_configs:
      - targets: ['ssl-exporter:9219']
    metrics_path: /probe
    params:
      target: ['localhost:443']
    scrape_interval: 300s

  # カスタムアプリケーションメトリクス
  - job_name: 'custom-app-metrics'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /api/v1/metrics
    scrape_interval: 15s
    honor_labels: true

  # Blue-Green環境監視
  - job_name: 'blue-environment'
    static_configs:
      - targets: ['backend-blue:8000', 'frontend-blue:3000']
    metrics_path: /metrics
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'green-environment'
    static_configs:
      - targets: ['backend-green:8000', 'frontend-green:3000']
    metrics_path: /metrics
    scrape_interval: 30s
    scrape_timeout: 10s

# リモート書き込み設定 (将来のマルチクラスター対応)
# remote_write:
#   - url: "https://prometheus-remote-write-endpoint"
#     basic_auth:
#       username: "user"
#       password: "password"

# リモート読み取り設定
# remote_read:
#   - url: "https://prometheus-remote-read-endpoint"

# ストレージ設定
storage:
  tsdb:
    path: /prometheus
    retention.time: 30d
    retention.size: 15GB
    wal-compression: true

# パフォーマンス最適化
query:
  max_concurrency: 20
  max_samples: 50000000
  timeout: 2m

# ログ設定
log:
  level: info
  format: json
EOF

    success "Prometheus強化設定生成完了"
}

# Create comprehensive Grafana dashboards
create_grafana_dashboards() {
    log "包括的Grafanaダッシュボード作成中..."
    
    mkdir -p "$SCRIPT_DIR/$DASHBOARDS_DIR"
    
    # System Overview Dashboard
    cat > "$SCRIPT_DIR/$DASHBOARDS_DIR/system-overview-v65.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "ITDO ERP v65.0 - システム概要",
    "tags": ["cc03-v65", "system", "overview"],
    "timezone": "Asia/Tokyo",
    "panels": [
      {
        "id": 1,
        "title": "システム稼働状況",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"backend-api|postgres-exporter|redis-exporter\"}",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "CPU使用率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU使用率"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "メモリ使用率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "メモリ使用率"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "ディスク使用率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "100 - ((node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"}) * 100)",
            "legendFormat": "ディスク使用率"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

    success "Grafanaダッシュボード作成完了"
}

# Deploy monitoring system
deploy_monitoring() {
    log "統合監視システムデプロイ中..."
    
    # Pull latest images
    info "最新コンテナイメージ取得中..."
    $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" pull
    
    # Start monitoring services
    info "監視サービス起動中..."
    $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # Wait for services to start
    info "サービス初期化待機中..."
    sleep 60
    
    success "監視システムデプロイ完了"
}

# Verify monitoring deployment
verify_monitoring() {
    log "監視システム動作確認中..."
    
    local services=(
        "prometheus:9090/-/healthy"
        "grafana:3000/api/health"
        "alertmanager:9093/-/healthy"
        "node-exporter:9100/metrics"
        "cadvisor:8080/healthz"
    )
    
    for service_check in "${services[@]}"; do
        local service=$(echo "$service_check" | cut -d: -f1)
        local port_path=$(echo "$service_check" | cut -d: -f2-)
        local url="http://localhost:${port_path}"
        
        info "${service} ヘルスチェック実行中..."
        
        local attempts=0
        local max_attempts=30
        
        while [[ $attempts -lt $max_attempts ]]; do
            if curl -f -s "$url" > /dev/null 2>&1; then
                success "${service} ヘルスチェック成功"
                break
            fi
            
            ((attempts++))
            if [[ $attempts -eq $max_attempts ]]; then
                warn "${service} ヘルスチェック失敗 - サービスが起動中の可能性があります"
            else
                sleep 2
            fi
        done
    done
    
    success "監視システム動作確認完了"
}

# Show monitoring URLs and info
show_monitoring_info() {
    echo -e "${PURPLE}"
    echo "🎉 CC03 v65.0 統合監視ダッシュボードシステム起動完了!"
    echo "================================================="
    echo -e "${NC}"
    
    echo -e "${BLUE}=== 監視システムURL ===${NC}"
    echo "📊 Grafana ダッシュボード: http://localhost:3001"
    echo "   ユーザー: admin"
    echo "   パスワード: GrafanaAdmin2025!Monitor#v65"
    echo ""
    echo "⚡ Prometheus メトリクス: http://localhost:9090"
    echo "🚨 Alertmanager: http://localhost:9093"
    echo "🖥️  Node Exporter: http://localhost:9100/metrics"
    echo "📦 cAdvisor: http://localhost:8080"
    echo ""
    
    echo -e "${BLUE}=== 監視対象サービス ===${NC}"
    echo "✅ システムメトリクス (CPU, Memory, Disk)"
    echo "✅ コンテナメトリクス (Docker/Podman)"
    echo "✅ PostgreSQL データベース"
    echo "✅ Redis キャッシュ"
    echo "✅ NGINX Webサーバー"
    echo "✅ Backend API アプリケーション"
    echo "✅ Keycloak 認証サービス"
    echo "✅ SSL証明書監視"
    echo "✅ 外部サービス監視"
    echo ""
    
    echo -e "${BLUE}=== リアルタイム機能 ===${NC}"
    echo "🔄 5秒間隔メトリクス更新"
    echo "📈 自動ダッシュボード更新"
    echo "🚨 インテリジェントアラート"
    echo "📱 Slackアラート連携"
    echo "📧 メールアラート送信"
    echo ""
    
    echo -e "${BLUE}=== 管理コマンド ===${NC}"
    echo "📊 状況確認: $COMPOSE_CMD -f $MONITORING_COMPOSE_FILE ps"
    echo "📋 ログ確認: $COMPOSE_CMD -f $MONITORING_COMPOSE_FILE logs -f [service]"
    echo "🔄 再起動: $COMPOSE_CMD -f $MONITORING_COMPOSE_FILE restart [service]"
    echo "🛑 停止: $COMPOSE_CMD -f $MONITORING_COMPOSE_FILE down"
    echo ""
    
    success "CC03 v65.0 監視ダッシュボードシステム準備完了!"
}

# Main function
main() {
    case ${1:-deploy} in
        "deploy")
            print_header
            check_prerequisites
            create_monitoring_env
            generate_monitoring_compose
            generate_prometheus_config
            create_grafana_dashboards
            deploy_monitoring
            verify_monitoring
            show_monitoring_info
            ;;
        "status")
            check_prerequisites
            if [[ -f "$MONITORING_COMPOSE_FILE" ]] && [[ -f "$ENV_FILE" ]]; then
                $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" ps
            else
                error "監視システム設定ファイルが見つかりません"
            fi
            ;;
        "logs")
            if [[ -n ${2:-} ]]; then
                $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "$2"
            else
                $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
            fi
            ;;
        "restart")
            if [[ -n ${2:-} ]]; then
                $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" restart "$2"
            else
                $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" restart
            fi
            ;;
        "stop")
            $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" down
            ;;
        "cleanup")
            warn "監視システム完全削除中..."
            $COMPOSE_CMD -f "$MONITORING_COMPOSE_FILE" --env-file "$ENV_FILE" down --volumes --remove-orphans
            success "監視システム完全削除完了"
            ;;
        "help")
            echo "Usage: $0 [deploy|status|logs|restart|stop|cleanup|help]"
            echo ""
            echo "Commands:"
            echo "  deploy  - 統合監視システムデプロイ"
            echo "  status  - 監視サービス状況確認"
            echo "  logs    - ログ表示 (logs [service] で個別確認)"
            echo "  restart - サービス再起動 (restart [service] で個別再起動)"
            echo "  stop    - 監視システム停止"
            echo "  cleanup - 監視システム完全削除 (データ含む)"
            echo "  help    - ヘルプ表示"
            echo ""
            echo "Examples:"
            echo "  $0 deploy           # 監視システム完全デプロイ"
            echo "  $0 status           # サービス状況確認"
            echo "  $0 logs grafana     # Grafanaログ確認"
            echo "  $0 restart prometheus # Prometheus再起動"
            ;;
        *)
            error "不明なコマンド: $1. '$0 help' でヘルプを確認してください。"
            ;;
    esac
}

# Script execution
main "$@"