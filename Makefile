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
