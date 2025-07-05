.PHONY: help dev test test-full lint typecheck clean setup-dev start-data stop-data status build security-scan pre-commit

help:
	@echo "利用可能なコマンド:"
	@echo "  make dev           - 開発サーバーを起動"
	@echo "  make test          - 基本テストを実行"
	@echo "  make test-full     - 包括的テストを実行（E2E含む）"
	@echo "  make lint          - リントを実行"
	@echo "  make typecheck     - 型チェックを実行"
	@echo "  make security-scan - セキュリティスキャンを実行"
	@echo "  make setup-dev     - 開発環境をセットアップ"
	@echo "  make start-data    - データ層を起動"
	@echo "  make stop-data     - データ層を停止"
	@echo "  make status        - サービス状態を確認"
	@echo "  make build         - コンテナイメージをビルド"
	@echo "  make pre-commit    - pre-commitフックをセットアップ"
	@echo "  make clean         - 一時ファイルを削除"

dev:
	@echo "開発サーバーを起動中..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "停止するには Ctrl+C を押してください"
	@(cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

test:
	@echo "基本テストを実行中..."
	@./scripts/test.sh --no-e2e

test-full:
	@echo "包括的テストを実行中（E2E含む）..."
	@./scripts/test.sh

lint:
	@echo "バックエンドリントを実行中..."
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv run ruff check . && uv run ruff format .
	@echo "フロントエンドリントを実行中..."
	@cd frontend && npm run lint

typecheck:
	@echo "バックエンド型チェックを実行中..."
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv run mypy --strict app/
	@echo "フロントエンド型チェックを実行中..."
	@cd frontend && npm run typecheck

security-scan:
	@echo "セキュリティスキャンを実行中..."
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv pip install bandit[toml] safety
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv run bandit -r app/ -f text
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv run safety check
	@cd frontend && npm audit --audit-level=moderate

setup-dev:
	@echo "開発環境をセットアップ中..."
	@./scripts/init-project.sh

start-data:
	@echo "データ層を起動中..."
	@export PATH="$$HOME/.local/bin:$$PATH" && podman-compose -f infra/compose-data.yaml up -d

stop-data:
	@echo "データ層を停止中..."
	@export PATH="$$HOME/.local/bin:$$PATH" && podman-compose -f infra/compose-data.yaml down

status:
	@echo "サービス状態を確認中..."
	@export PATH="$$HOME/.local/bin:$$PATH" && podman-compose -f infra/compose-data.yaml ps

build:
	@echo "コンテナイメージをビルド中..."
	@docker build -t itdo-erp-backend:latest ./backend
	@docker build -t itdo-erp-frontend:latest ./frontend

pre-commit:
	@echo "pre-commitフックをセットアップ中..."
	@cd backend && export PATH="$$HOME/.local/bin:$$PATH" && uv pip install pre-commit
	@export PATH="$$HOME/.local/bin:$$PATH" && pre-commit install
	@export PATH="$$HOME/.local/bin:$$PATH" && pre-commit run --all-files

clean:
	@echo "一時ファイルを削除中..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf backend/.pytest_cache frontend/node_modules/.cache
	@rm -rf test-reports/
	@rm -rf backend/htmlcov/ frontend/coverage/
	@rm -rf e2e/test-results/ e2e/playwright-report/
