#!/bin/bash
# Claude Code エージェント初期化スクリプト v2 - 強化版
# 信頼性向上のための改善を実装

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: source scripts/claude-code-automation/agent/agent-init-v2.sh [CC01|CC02|CC03]"
    return 1 2>/dev/null || exit 1
fi

AGENT_ID=$1
export CLAUDE_AGENT_ID=$AGENT_ID

# 色付け
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 状態ファイルのパス
STATE_DIR="$HOME/.claude-code-automation"
STATE_FILE="$STATE_DIR/agent-$AGENT_ID.state"
LOG_FILE="$STATE_DIR/agent-$AGENT_ID.log"

# 状態ディレクトリの作成
mkdir -p "$STATE_DIR"

# 初期化開始
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    Claude Code $AGENT_ID 初期化中 (v2)...                      ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 初期化ログ開始
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initialization started for $AGENT_ID" >> "$LOG_FILE"

# 1. 作業ディレクトリ確認
log_info "作業環境確認中..."
if [ -d "$PROJECT_ROOT/.git" ]; then
    cd "$PROJECT_ROOT"
    log_success "作業ディレクトリ: $PROJECT_ROOT"
else
    log_error "プロジェクトディレクトリが見つかりません"
    return 1 2>/dev/null || exit 1
fi

# 2. 必要なツールの確認
log_info "必要なツールを確認中..."
MISSING_TOOLS=()

command -v git >/dev/null 2>&1 || MISSING_TOOLS+=("git")
command -v gh >/dev/null 2>&1 || MISSING_TOOLS+=("gh")

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    log_error "以下のツールがインストールされていません: ${MISSING_TOOLS[*]}"
    return 1 2>/dev/null || exit 1
fi
log_success "必要なツールが全て利用可能です"

# 3. Git設定
log_info "Git設定を更新中..."
git config user.name "Claude Code $AGENT_ID" 2>/dev/null || log_warning "Git user.name設定失敗"
git config user.email "claude-${AGENT_ID,,}@itdo.jp" 2>/dev/null || log_warning "Git user.email設定失敗"
log_success "Git設定完了"

# 4. GitHub CLI認証確認
log_info "GitHub CLI認証を確認中..."
if gh auth status >/dev/null 2>&1; then
    log_success "GitHub CLI認証済み"
else
    log_warning "GitHub CLIが認証されていません。'gh auth login'を実行してください"
fi

# 5. 最新の状態に更新
log_info "リポジトリを更新中..."
if git pull origin main --quiet 2>/dev/null; then
    log_success "リポジトリ更新完了"
else
    log_warning "更新をスキップ（オフラインまたは変更あり）"
fi

# 6. エイリアス設定
log_info "便利なエイリアスを設定中..."
alias my-tasks="gh issue list --label '${AGENT_ID,,}' --state open"
alias my-pr="gh pr list --author @me"
alias check-ci="gh pr checks"
alias daily-report="$SCRIPT_DIR/agent-daily-report.sh"
alias fix-ci="$SCRIPT_DIR/auto-fix-ci.sh"
alias task-done="gh issue close"
alias agent-status="cat $STATE_FILE 2>/dev/null || echo 'No state found'"
alias agent-logs="tail -n 50 $LOG_FILE"

# エイリアスを状態ファイルに保存
cat > "$STATE_FILE" <<EOF
AGENT_ID=$AGENT_ID
INITIALIZED_AT=$(date '+%Y-%m-%d %H:%M:%S')
PROJECT_ROOT=$PROJECT_ROOT
LOG_FILE=$LOG_FILE
EOF

log_success "エイリアス設定完了"
echo "  ✓ my-tasks     : 自分のタスク一覧"
echo "  ✓ my-pr        : 自分のPR一覧"
echo "  ✓ check-ci     : CI/CD状態確認"
echo "  ✓ agent-status : エージェント状態確認"
echo "  ✓ agent-logs   : 最近のログ表示"

# 7. 現在のタスク確認
log_info "現在のタスクを確認中..."
TASKS=$(gh issue list --label "${AGENT_ID,,}" --state open --json number,title --jq '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
if [ -z "$TASKS" ]; then
    echo "  現在割り当てられたタスクはありません"
else
    echo -e "${YELLOW}📋 現在のタスク:${NC}"
    echo "$TASKS"
fi

# 8. 環境変数エクスポート
export AGENT_LABEL="${AGENT_ID,,}"
export AGENT_PROMPT="[$AGENT_ID]"
export CLAUDE_PROJECT_ROOT="$PROJECT_ROOT"
export CLAUDE_AGENT_STATE_FILE="$STATE_FILE"
export CLAUDE_AGENT_LOG_FILE="$LOG_FILE"

# 9. プロンプト変更（オプション）
PS1="🤖 $AGENT_ID \w $ "

# 10. ヘルスチェック機能
health_check() {
    echo "🏥 エージェント ヘルスチェック"
    echo "================================"
    echo "Agent ID: $CLAUDE_AGENT_ID"
    echo "Project Root: $CLAUDE_PROJECT_ROOT"
    echo "State File: $CLAUDE_AGENT_STATE_FILE"
    echo "Log File: $CLAUDE_AGENT_LOG_FILE"
    echo ""
    echo "GitHub Status:"
    gh auth status 2>&1 | head -3
    echo ""
    echo "Current Tasks:"
    gh issue list --label "${AGENT_ID,,}" --state open --json number,title | head -5
}

alias health-check="health_check"

# 11. 自動ポーリング設定（改善版）
if [ -z "$CLAUDE_NO_AUTO_POLLING" ]; then
    log_info "自動タスクチェックを設定中..."
    
    # 既存のポーリングプロセスを停止
    pkill -f "agent-work-polling-$AGENT_ID" 2>/dev/null || true
    
    # 新しいポーリングプロセスを開始
    (
        while true; do
            sleep 900  # 15分（900秒）
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-check running" >> "$LOG_FILE"
            echo -e "\n${BLUE}[$(date '+%H:%M')] 定期タスクチェック${NC}"
            "$SCRIPT_DIR/agent-work.sh" 2>>"$LOG_FILE" || echo "Auto-check failed" >> "$LOG_FILE"
        done
    ) &
    POLLING_PID=$!
    
    # ポーリングPIDを状態ファイルに保存
    echo "POLLING_PID=$POLLING_PID" >> "$STATE_FILE"
    
    log_success "自動ポーリング開始 (PID: $POLLING_PID)"
    echo "  停止する場合: kill $POLLING_PID"
fi

# 12. 完了メッセージ
echo -e "\n${GREEN}✅ 初期化完了！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "💡 新機能:"
echo "  - 'health-check' でシステム状態を確認"
echo "  - 'agent-status' でエージェント状態を表示"
echo "  - 'agent-logs' で最近のログを確認"
echo "  - 状態は '$STATE_FILE' に永続化されます"
echo ""
echo "📝 次のステップ:"
echo "  1. 'my-tasks' で割り当てられたタスクを確認"
echo "  2. 'health-check' でシステム状態を確認"
echo "  3. 問題がある場合は 'agent-logs' でログを確認"
echo ""

# 初期化成功をログに記録
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initialization completed successfully" >> "$LOG_FILE"

# 初期化成功を返す
return 0 2>/dev/null || exit 0