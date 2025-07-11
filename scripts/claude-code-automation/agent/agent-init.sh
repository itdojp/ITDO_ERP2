#!/bin/bash
# Claude Code エージェント初期化スクリプト

set -e

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: source scripts/agent-init.sh [CC01|CC02|CC03]"
    return 1 2>/dev/null || exit 1
fi

AGENT_ID=$1
export CLAUDE_AGENT_ID=$AGENT_ID

# 色付け
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    Claude Code $AGENT_ID 初期化中...                           ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 作業ディレクトリ確認
echo -e "\n${YELLOW}📁 作業環境設定${NC}"
cd /mnt/c/work/ITDO_ERP2 2>/dev/null || { echo "エラー: プロジェクトディレクトリが見つかりません"; return 1; }
echo "  ✓ 作業ディレクトリ: $(pwd)"

# Git設定
git config user.name "Claude Code $AGENT_ID" 2>/dev/null || true
git config user.email "claude-${AGENT_ID,,}@itdo.jp" 2>/dev/null || true
echo "  ✓ Git設定完了"

# 最新の状態に更新
echo -e "\n${YELLOW}🔄 リポジトリ更新${NC}"
git pull origin main --quiet 2>/dev/null || echo "  ⚠️  更新をスキップ（オフラインまたは変更あり）"

# エイリアス設定
echo -e "\n${YELLOW}⚙️  便利なエイリアス設定${NC}"
alias my-tasks="gh issue list --label '${AGENT_ID,,}' --state open"
alias my-pr="gh pr list --author @me"
alias check-ci="gh pr checks"
alias daily-report="./scripts/agent-daily-report.sh"
alias fix-ci="./scripts/auto-fix-ci.sh"
alias task-done="gh issue close"

echo "  ✓ my-tasks    : 自分のタスク一覧"
echo "  ✓ my-pr       : 自分のPR一覧"
echo "  ✓ check-ci    : CI/CD状態確認"
echo "  ✓ daily-report: 日次レポート生成"
echo "  ✓ fix-ci      : CI/CD自動修正"

# 現在のタスク確認
echo -e "\n${YELLOW}📋 現在のタスク${NC}"
TASKS=$(gh issue list --label "${AGENT_ID,,}" --state open --json number,title --jq '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
if [ -z "$TASKS" ]; then
    echo "  現在割り当てられたタスクはありません"
else
    echo "$TASKS"
fi

# 環境変数エクスポート
export AGENT_LABEL="${AGENT_ID,,}"
export AGENT_PROMPT="[$AGENT_ID]"

# プロンプト変更（オプション）
PS1="🤖 $AGENT_ID \w $ "

# 完了メッセージ
echo -e "\n${GREEN}✅ 初期化完了！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "💡 ヒント:"
echo "  - 'my-tasks' で自分のタスクを確認"
echo "  - './scripts/agent-work.sh' で自動作業実行"
echo "  - 'make agent-status' で全体状況確認"
echo ""