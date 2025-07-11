#!/bin/bash
# Claude Code エージェント初期化スクリプト v2
# 改善版：信頼性向上と状態永続化

set -e

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: source scripts/claude-code-automation/agent/agent-init-v2.sh [CC01|CC02|CC03]"
    return 1 2>/dev/null || exit 1
fi

AGENT_ID=$1
STATE_FILE="$HOME/.claude-agent-state"

# 色付け
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# ========================================
# 1. 状態の復元（セッション永続化）
# ========================================
restore_agent_state() {
    if [ -f "$STATE_FILE" ]; then
        source "$STATE_FILE"
        echo -e "${BLUE}♻️  前回の状態を復元しました: $CLAUDE_AGENT_ID${NC}"
        
        # 前回のセッションから30分以上経過している場合は警告
        if [ ! -z "$LAST_ACTIVE" ]; then
            CURRENT_TIME=$(date +%s)
            TIME_DIFF=$((CURRENT_TIME - LAST_ACTIVE))
            if [ $TIME_DIFF -gt 1800 ]; then
                echo -e "${YELLOW}⚠️  前回のセッションから$(($TIME_DIFF / 60))分経過しています${NC}"
            fi
        fi
    fi
}

# ========================================
# 2. 状態の保存
# ========================================
save_agent_state() {
    cat > "$STATE_FILE" << EOF
# Claude Agent State File
CLAUDE_AGENT_ID=$CLAUDE_AGENT_ID
AGENT_LABEL=$AGENT_LABEL
LAST_ACTIVE=$(date +%s)
SESSION_ID=$$
POLLING_PID=$POLLING_PID
EOF
    echo -e "${GREEN}✓ 状態を保存しました${NC}"
}

# ========================================
# 3. 初期化と検証を統合
# ========================================
init_agent() {
    local agent_id=$1
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}                    Claude Code $agent_id 初期化中 (v2)...                           ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # 1. 環境変数設定
    export CLAUDE_AGENT_ID=$agent_id
    export AGENT_LABEL="${agent_id,,}"
    export AGENT_PROMPT="[$agent_id]"
    
    # 2. 必須チェック
    if [ -z "$CLAUDE_AGENT_ID" ]; then
        echo -e "${RED}❌ ERROR: Agent ID設定失敗${NC}"
        return 1
    fi
    
    # 3. プロンプト変更
    PS1="🤖 $agent_id \w $ "
    
    # 4. 成功確認
    echo -e "${GREEN}✅ SUCCESS: $agent_id 初期化完了${NC}"
    return 0
}

# ========================================
# 4. プロセス監視機能
# ========================================
check_polling_health() {
    if [ ! -z "$POLLING_PID" ] && kill -0 $POLLING_PID 2>/dev/null; then
        echo -e "${GREEN}✓ ポーリングプロセス動作中 (PID: $POLLING_PID)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  ポーリングプロセスが停止しています${NC}"
        return 1
    fi
}

# ========================================
# 5. 強化されたポーリング起動
# ========================================
start_polling_process() {
    # 既存のポーリングを停止
    if [ ! -z "$POLLING_PID" ] && kill -0 $POLLING_PID 2>/dev/null; then
        echo -e "${YELLOW}既存のポーリングを停止中...${NC}"
        kill $POLLING_PID 2>/dev/null || true
        sleep 1
    fi
    
    # 新しいポーリングを開始（エラーハンドリング付き）
    (
        while true; do
            sleep 900  # 15分（900秒）
            echo -e "\n${BLUE}[$(date '+%H:%M')] 定期タスクチェック${NC}"
            
            # タスク実行とエラーチェック
            if ! "$SCRIPT_DIR/agent-work.sh" 2>&1; then
                echo -e "${RED}⚠️  タスク実行中にエラーが発生しました${NC}"
                
                # エラーを Issue #99 に報告
                gh issue comment 99 --body "## ⚠️ 自動エラー報告 - $CLAUDE_AGENT_ID

**時刻**: $(date '+%Y-%m-%d %H:%M:%S')
**エラー**: agent-work.sh 実行失敗
**プロセス状態**: ポーリング継続中

自動リトライを15分後に実行します。" 2>/dev/null || true
            fi
            
            # 状態を更新
            LAST_ACTIVE=$(date +%s)
            save_agent_state
        done
    ) &
    POLLING_PID=$!
    
    echo -e "${GREEN}✓ 強化されたポーリング開始 (PID: $POLLING_PID)${NC}"
}

# ========================================
# 6. 検証関数
# ========================================
verify_setup() {
    local success=true
    
    echo -e "\n${YELLOW}🔍 環境検証中...${NC}"
    
    # Agent ID確認
    if [ ! -z "$CLAUDE_AGENT_ID" ]; then
        echo -e "  ${GREEN}✓ Agent ID: $CLAUDE_AGENT_ID${NC}"
    else
        echo -e "  ${RED}✗ Agent ID: 未設定${NC}"
        success=false
    fi
    
    # GitHub CLI認証確認
    if gh auth status &>/dev/null; then
        echo -e "  ${GREEN}✓ GitHub CLI: 認証済み${NC}"
    else
        echo -e "  ${RED}✗ GitHub CLI: 未認証${NC}"
        success=false
    fi
    
    # エイリアス確認
    if command -v my-tasks &>/dev/null; then
        echo -e "  ${GREEN}✓ エイリアス: 設定済み${NC}"
    else
        echo -e "  ${YELLOW}⚠️  エイリアス: 未設定（手動設定が必要）${NC}"
    fi
    
    # ポーリング確認
    if check_polling_health; then
        echo -e "  ${GREEN}✓ ポーリング: 動作中${NC}"
    else
        echo -e "  ${YELLOW}⚠️  ポーリング: 停止中${NC}"
    fi
    
    if [ "$success" = true ]; then
        echo -e "\n${GREEN}✅ 全ての検証に成功しました${NC}"
        return 0
    else
        echo -e "\n${RED}❌ 一部の検証に失敗しました${NC}"
        return 1
    fi
}

# ========================================
# メイン実行
# ========================================

# 前回の状態を復元
restore_agent_state

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
if git pull origin main --quiet 2>/dev/null; then
    echo "  ✓ 最新のコードに更新しました"
else
    echo "  ⚠️  更新をスキップ（オフラインまたは変更あり）"
fi

# エイリアス設定（関数として定義）
echo -e "\n${YELLOW}⚙️  便利な機能を設定${NC}"

# my-tasks 関数
my-tasks() {
    gh issue list --label "${AGENT_LABEL}" --state open
}
export -f my-tasks

# その他のエイリアス
alias my-pr="gh pr list --author @me"
alias check-ci="gh pr checks"
alias fix-ci="$SCRIPT_DIR/auto-fix-ci.sh"
alias agent-status="$SCRIPT_DIR/../pm/agent-status.sh"

echo "  ✓ my-tasks    : 自分のタスク一覧"
echo "  ✓ my-pr       : 自分のPR一覧"
echo "  ✓ check-ci    : CI/CD状態確認"
echo "  ✓ fix-ci      : CI/CD自動修正"
echo "  ✓ agent-status: 全体状況確認"

# 初期化実行
init_agent $AGENT_ID

# 現在のタスク確認
echo -e "\n${YELLOW}📋 現在のタスク${NC}"
TASKS=$(gh issue list --label "${AGENT_LABEL}" --state open --json number,title --jq '.[] | "  #\(.number): \(.title)"' 2>/dev/null)
if [ -z "$TASKS" ]; then
    echo "  現在割り当てられたタスクはありません"
else
    echo "$TASKS"
fi

# ポーリング開始
echo -e "\n${YELLOW}⏰ 自動タスクチェック設定${NC}"
if [ -z "$CLAUDE_NO_AUTO_POLLING" ]; then
    start_polling_process
else
    echo "  自動ポーリングは無効化されています"
fi

# 状態を保存
save_agent_state

# 最終検証
verify_setup

# 完了メッセージ
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}                           初期化完了！(v2)                                            ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "💡 使い方:"
echo "  - 'my-tasks' で自分のタスクを確認"
echo "  - '$SCRIPT_DIR/agent-work.sh' で即座に作業実行"
echo "  - 'agent-status' で全体状況確認"
echo "  - 'verify_setup' で環境を再検証"
echo ""
echo "📊 改善点:"
echo "  - セッション間での状態永続化"
echo "  - エラー時の自動報告"
echo "  - プロセス監視機能"
echo "  - 検証機能の統合"
echo ""