#!/bin/bash
# 開発環境自動化スクリプト
# CC03作成 - ローカル開発効率化ツール

set -e

# 色付きログ出力
log_info() { echo -e "\033[32m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# 環境チェック関数
check_environment() {
    log_info "開発環境チェック開始..."
    
    # Python環境チェック
    if command -v uv >/dev/null 2>&1; then
        log_info "✓ uv package manager: $(uv --version)"
    else
        log_error "✗ uv not found. Please install uv package manager"
        exit 1
    fi
    
    # Node.js環境チェック
    if command -v node >/dev/null 2>&1; then
        log_info "✓ Node.js: $(node --version)"
    else
        log_warn "✗ Node.js not found"
    fi
    
    # Git環境チェック
    if command -v git >/dev/null 2>&1; then
        log_info "✓ Git: $(git --version)"
    else
        log_error "✗ Git not found"
        exit 1
    fi
    
    # GitHub CLI チェック
    if command -v gh >/dev/null 2>&1; then
        log_info "✓ GitHub CLI: $(gh --version | head -1)"
    else
        log_warn "✗ GitHub CLI not found - PR operations limited"
    fi
}

# 依存関係自動インストール
setup_dependencies() {
    log_info "依存関係のセットアップ..."
    
    # Backend dependencies
    if [ -f "backend/pyproject.toml" ]; then
        log_info "Backend dependencies installing..."
        cd backend
        uv sync
        cd ..
        log_info "✓ Backend dependencies installed"
    fi
    
    # Frontend dependencies
    if [ -f "frontend/package.json" ]; then
        log_info "Frontend dependencies installing..."
        cd frontend
        npm install
        cd ..
        log_info "✓ Frontend dependencies installed"
    fi
}

# 品質チェック実行
run_quality_checks() {
    log_info "品質チェック実行..."
    
    cd backend
    
    # Ruff linting
    log_info "Running ruff linting..."
    uv run ruff check .
    if [ $? -eq 0 ]; then
        log_info "✓ Ruff linting passed"
    else
        log_error "✗ Ruff linting failed"
        return 1
    fi
    
    # Core Foundation Tests
    log_info "Running Core Foundation Tests..."
    uv run pytest tests/test_main.py -v
    if [ $? -eq 0 ]; then
        log_info "✓ Core Foundation Tests passed"
    else
        log_error "✗ Core Foundation Tests failed"
        return 1
    fi
    
    cd ..
}

# 開発サーバー起動準備
prepare_dev_servers() {
    log_info "開発サーバー起動準備..."
    
    # データレイヤーコンテナ状態チェック
    if command -v podman-compose >/dev/null 2>&1; then
        log_info "Checking data layer containers..."
        # Note: 実際のコンテナ操作は必要に応じて実行
        log_info "✓ Container management available"
    else
        log_warn "✗ podman-compose not found - manual container management needed"
    fi
    
    # 環境変数チェック
    if [ -f "backend/.env" ]; then
        log_info "✓ Backend .env file found"
    else
        log_warn "✗ Backend .env file not found - may need manual setup"
    fi
}

# 開発状況レポート生成
generate_dev_report() {
    log_info "開発状況レポート生成..."
    
    REPORT_FILE="CC03_DEV_STATUS_$(date +%Y%m%d_%H%M).md"
    
    cat > "$REPORT_FILE" << EOF
# 開発環境自動化レポート

**生成日時**: $(date)
**実行者**: CC03 Dev Automation Script

## 環境状況

### システム情報
- OS: $(uname -s)
- アーキテクチャ: $(uname -m)
- 現在時刻: $(date)

### 開発ツール
- Python (uv): $(uv --version 2>/dev/null || echo "Not available")
- Node.js: $(node --version 2>/dev/null || echo "Not available")
- Git: $(git --version 2>/dev/null || echo "Not available")
- GitHub CLI: $(gh --version 2>/dev/null | head -1 || echo "Not available")

### プロジェクト状況
- Git branch: $(git branch --show-current 2>/dev/null || echo "Unknown")
- Git status: $(git status --porcelain 2>/dev/null | wc -l) files modified
- Last commit: $(git log -1 --format="%h %s" 2>/dev/null || echo "Unknown")

### ローカル品質状況
EOF

    # 品質チェック結果を追加
    cd backend
    echo "- Ruff linting: $(uv run ruff check . >/dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL")" >> "../$REPORT_FILE"
    echo "- Core Tests: $(uv run pytest tests/test_main.py -q >/dev/null 2>&1 && echo "✓ PASS" || echo "✗ FAIL")" >> "../$REPORT_FILE"
    cd ..
    
    cat >> "$REPORT_FILE" << EOF

## 推奨アクション
1. データレイヤーコンテナ起動: \`make start-data\`
2. 開発サーバー起動: \`make dev\`
3. 品質チェック実行: \`make lint && make test\`

---
生成者: CC03 Development Automation System
EOF

    log_info "✓ レポート生成完了: $REPORT_FILE"
}

# メイン実行関数
main() {
    log_info "=== CC03 開発環境自動化スクリプト ==="
    
    case "${1:-check}" in
        "check")
            check_environment
            ;;
        "setup")
            check_environment
            setup_dependencies
            ;;
        "quality")
            run_quality_checks
            ;;
        "prepare")
            check_environment
            setup_dependencies
            prepare_dev_servers
            ;;
        "report")
            generate_dev_report
            ;;
        "full")
            check_environment
            setup_dependencies
            run_quality_checks
            prepare_dev_servers
            generate_dev_report
            ;;
        *)
            echo "Usage: $0 {check|setup|quality|prepare|report|full}"
            echo ""
            echo "Commands:"
            echo "  check    - 環境チェックのみ"
            echo "  setup    - 依存関係セットアップ"
            echo "  quality  - 品質チェック実行"
            echo "  prepare  - 開発サーバー準備"
            echo "  report   - 開発状況レポート生成"
            echo "  full     - 全処理実行"
            exit 1
            ;;
    esac
    
    log_info "=== 処理完了 ==="
}

# スクリプト実行
main "$@"