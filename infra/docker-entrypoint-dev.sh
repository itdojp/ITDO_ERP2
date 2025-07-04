#!/bin/bash
set -e

echo "開発環境の初期化を開始します..."

# データベースの接続待機
echo "データベース接続を待機中..."
until nc -z postgres 5432; do
    echo "PostgreSQLの起動を待機中..."
    sleep 2
done

echo "Redis接続を待機中..."
until nc -z redis 6379; do
    echo "Redisの起動を待機中..."
    sleep 2
done

echo "Keycloak接続を待機中..."
until nc -z keycloak 8080; do
    echo "Keycloakの起動を待機中..."
    sleep 2
done

echo "全サービスが利用可能になりました。"
echo "開発環境の準備が完了しました。"
echo ""
echo "利用可能なコマンド:"
echo "  make dev        - 開発サーバーを起動"
echo "  make test       - テストを実行"
echo "  make lint       - リントを実行"
echo "  make typecheck  - 型チェックを実行"
echo ""

# シェルを開始
exec "$@"