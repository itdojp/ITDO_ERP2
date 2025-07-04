#!/bin/bash

# ITDO ERP System - Development Environment Management Script
# This script manages the development environment containers

set -e

COMPOSE_FILE="infra/compose-data.yaml"
DEV_COMPOSE_FILE="infra/compose-dev.yaml"

usage() {
    echo "Usage: $0 {start|stop|restart|logs|shell|status|full-start|full-stop}"
    echo ""
    echo "Commands:"
    echo "  start       - データ層のみ起動 (推奨)"
    echo "  stop        - データ層のみ停止"
    echo "  restart     - データ層の再起動"
    echo "  logs        - ログを表示"
    echo "  shell       - データベースシェルに接続"
    echo "  status      - コンテナの状態を確認"
    echo "  full-start  - フルコンテナ開発環境を起動"
    echo "  full-stop   - フルコンテナ開発環境を停止"
    echo ""
    echo "推奨開発フロー:"
    echo "1. ./scripts/dev-env.sh start"
    echo "2. make dev (別ターミナル)"
    exit 1
}

start_data_layer() {
    echo "🐘 データ層を起動中..."
    podman-compose -f $COMPOSE_FILE up -d
    echo "✅ データ層が起動しました"
    echo ""
    echo "利用可能なサービス:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  Keycloak: http://localhost:8080"
    echo "  PgAdmin: http://localhost:8081"
    echo ""
    echo "次のステップ: make dev で開発サーバーを起動"
}

stop_data_layer() {
    echo "🛑 データ層を停止中..."
    podman-compose -f $COMPOSE_FILE down
    echo "✅ データ層が停止しました"
}

restart_data_layer() {
    echo "🔄 データ層を再起動中..."
    podman-compose -f $COMPOSE_FILE restart
    echo "✅ データ層が再起動しました"
}

show_logs() {
    echo "📋 ログを表示中..."
    podman-compose -f $COMPOSE_FILE logs -f
}

connect_db_shell() {
    echo "🐘 PostgreSQL シェルに接続中..."
    podman exec -it itdo-postgres psql -U itdo_user -d itdo_erp
}

show_status() {
    echo "📊 コンテナの状態:"
    podman-compose -f $COMPOSE_FILE ps
}

start_full_dev() {
    echo "🚀 フルコンテナ開発環境を起動中..."
    podman-compose -f $DEV_COMPOSE_FILE up -d
    echo "✅ フルコンテナ開発環境が起動しました"
    echo ""
    echo "利用可能なサービス:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
    echo "  Keycloak: http://localhost:8080"
    echo "  Development Workspace: podman exec -it itdo-workspace-dev bash"
    echo ""
    echo "ワークスペースに接続: ./scripts/dev-env.sh shell"
}

stop_full_dev() {
    echo "🛑 フルコンテナ開発環境を停止中..."
    podman-compose -f $DEV_COMPOSE_FILE down
    echo "✅ フルコンテナ開発環境が停止しました"
}

connect_dev_shell() {
    echo "🐚 開発ワークスペースに接続中..."
    podman exec -it itdo-workspace-dev bash
}

case "${1:-}" in
    start)
        start_data_layer
        ;;
    stop)
        stop_data_layer
        ;;
    restart)
        restart_data_layer
        ;;
    logs)
        show_logs
        ;;
    shell)
        if podman ps --format "table {{.Names}}" | grep -q "itdo-workspace-dev"; then
            connect_dev_shell
        else
            connect_db_shell
        fi
        ;;
    status)
        show_status
        ;;
    full-start)
        start_full_dev
        ;;
    full-stop)
        stop_full_dev
        ;;
    *)
        usage
        ;;
esac