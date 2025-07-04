#!/bin/bash

# ITDO ERP System - Project Initialization Script
# This script initializes the development environment

set -e

echo "🚀 ITDO ERP System プロジェクト初期化開始"

# Check if running in correct directory
if [ ! -f "README.md" ]; then
    echo "❌ エラー: プロジェクトルートディレクトリで実行してください"
    exit 1
fi

# Check requirements
echo "📋 必要なツールの確認中..."

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ エラー: uv がインストールされていません"
    echo "インストール方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check podman or docker
if ! command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ エラー: podman または docker がインストールされていません"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ エラー: Node.js がインストールされていません"
    echo "推奨: Volta を使用してインストール"
    exit 1
fi

echo "✅ 必要なツールが確認されました"

# Backend setup
echo "🐍 Backend環境のセットアップ中..."
cd backend

# Create virtual environment
echo "Python仮想環境を作成中..."
uv venv

# Install dependencies
echo "Python依存関係をインストール中..."
uv pip install -r requirements.txt 2>/dev/null || echo "requirements.txt が見つかりません。後でインストールしてください。"

cd ..

# Frontend setup
echo "⚛️ Frontend環境のセットアップ中..."
cd frontend

# Install dependencies
echo "Node.js依存関係をインストール中..."
npm install

cd ..

# Create environment file
echo "🔧 環境設定ファイルを作成中..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Development Environment Configuration
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp
POSTGRES_SERVER=localhost
POSTGRES_USER=itdo_user
POSTGRES_PASSWORD=itdo_password
POSTGRES_DB=itdo_erp

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=itdo-erp
KEYCLOAK_CLIENT_ID=itdo-erp-client
KEYCLOAK_CLIENT_SECRET=

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
    echo "✅ .env ファイルを作成しました"
else
    echo "ℹ️  .env ファイルは既に存在します"
fi

# Create Makefile
echo "📝 Makefile を作成中..."
cat > Makefile << 'EOF'
.PHONY: help dev test lint typecheck clean

help:
	@echo "利用可能なコマンド:"
	@echo "  make dev        - 開発サーバーを起動"
	@echo "  make test       - テストを実行"
	@echo "  make lint       - リントを実行"
	@echo "  make typecheck  - 型チェックを実行"
	@echo "  make clean      - 一時ファイルを削除"

dev:
	@echo "開発サーバーを起動中..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "停止するには Ctrl+C を押してください"
	@(cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

test:
	@echo "バックエンドテストを実行中..."
	@cd backend && uv run pytest
	@echo "フロントエンドテストを実行中..."
	@cd frontend && npm test

lint:
	@echo "バックエンドリントを実行中..."
	@cd backend && uv run black . && uv run isort .
	@echo "フロントエンドリントを実行中..."
	@cd frontend && npm run lint

typecheck:
	@echo "バックエンド型チェックを実行中..."
	@cd backend && uv run mypy --strict .
	@echo "フロントエンド型チェックを実行中..."
	@cd frontend && npm run typecheck

clean:
	@echo "一時ファイルを削除中..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf backend/.pytest_cache frontend/node_modules/.cache
EOF

echo "✅ Makefile を作成しました"

echo ""
echo "🎉 プロジェクト初期化が完了しました！"
echo ""
echo "次のステップ:"
echo "1. データ層を起動: podman-compose -f infra/compose-data.yaml up -d"
echo "2. 開発サーバーを起動: make dev"
echo "3. ブラウザで http://localhost:3000 にアクセス"
echo ""
echo "その他のコマンド:"
echo "  make help  - 利用可能なコマンドを表示"
echo "  make test  - テストを実行"
echo "  make lint  - コードフォーマットを実行"
echo ""