#!/bin/bash
# エージェント健全性チェックツール

# 色付け
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    Claude Code エージェント健全性チェック                           ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ========================================
# 1. 環境変数チェック
# ========================================
echo -e "\n${YELLOW}🔍 環境変数チェック${NC}"

check_env() {
    local var_name=$1
    local var_value=${!var_name}
    
    if [ ! -z "$var_value" ]; then
        echo -e "  ${GREEN}✓ $var_name: $var_value${NC}"
        return 0
    else
        echo -e "  ${RED}✗ $var_name: 未設定${NC}"
        return 1
    fi
}

ENV_OK=true
check_env "CLAUDE_AGENT_ID" || ENV_OK=false
check_env "AGENT_LABEL" || ENV_OK=false
check_env "HOME" || ENV_OK=false

# ========================================
# 2. プロセスチェック
# ========================================
echo -e "\n${YELLOW}🔍 プロセスチェック${NC}"

# ポーリングプロセス
if pgrep -f "sleep 900" > /dev/null; then
    POLLING_PID=$(pgrep -f "sleep 900" | head -1)
    echo -e "  ${GREEN}✓ ポーリングプロセス: 動作中 (PID: $POLLING_PID)${NC}"
else
    echo -e "  ${RED}✗ ポーリングプロセス: 停止中${NC}"
fi

# agent-work プロセス
if pgrep -f "agent-work" > /dev/null; then
    echo -e "  ${GREEN}✓ agent-work: 実行中${NC}"
else
    echo -e "  ${YELLOW}○ agent-work: 待機中${NC}"
fi

# ========================================
# 3. GitHub CLI チェック
# ========================================
echo -e "\n${YELLOW}🔍 GitHub CLI チェック${NC}"

if gh auth status &>/dev/null; then
    echo -e "  ${GREEN}✓ 認証状態: 認証済み${NC}"
    
    # API接続テスト
    if gh api user &>/dev/null; then
        echo -e "  ${GREEN}✓ API接続: 正常${NC}"
    else
        echo -e "  ${RED}✗ API接続: 失敗${NC}"
    fi
else
    echo -e "  ${RED}✗ 認証状態: 未認証${NC}"
fi

# ========================================
# 4. ファイルシステムチェック
# ========================================
echo -e "\n${YELLOW}🔍 ファイルシステムチェック${NC}"

# 作業ディレクトリ
if [ -d "/mnt/c/work/ITDO_ERP2" ]; then
    echo -e "  ${GREEN}✓ 作業ディレクトリ: 存在${NC}"
else
    echo -e "  ${RED}✗ 作業ディレクトリ: 不明${NC}"
fi

# 状態ファイル
STATE_FILE="$HOME/.claude-agent-state"
if [ -f "$STATE_FILE" ]; then
    echo -e "  ${GREEN}✓ 状態ファイル: 存在${NC}"
    
    # 最終更新時刻
    if [ -r "$STATE_FILE" ]; then
        source "$STATE_FILE"
        if [ ! -z "$LAST_ACTIVE" ]; then
            CURRENT_TIME=$(date +%s)
            TIME_DIFF=$((CURRENT_TIME - LAST_ACTIVE))
            echo -e "  ${BLUE}  最終活動: $(($TIME_DIFF / 60))分前${NC}"
        fi
    fi
else
    echo -e "  ${YELLOW}○ 状態ファイル: なし${NC}"
fi

# ========================================
# 5. タスクチェック
# ========================================
echo -e "\n${YELLOW}🔍 タスクチェック${NC}"

if [ ! -z "$CLAUDE_AGENT_ID" ]; then
    TASK_COUNT=$(gh issue list --label "${CLAUDE_AGENT_ID,,}" --state open --json number --jq '. | length' 2>/dev/null || echo "0")
    
    if [ "$TASK_COUNT" -gt 0 ]; then
        echo -e "  ${GREEN}✓ オープンタスク: $TASK_COUNT 件${NC}"
        
        # 最新タスクを表示
        echo -e "  ${BLUE}最新のタスク:${NC}"
        gh issue list --label "${CLAUDE_AGENT_ID,,}" --state open --limit 3 --json number,title --jq '.[] | "    #\(.number): \(.title)"' 2>/dev/null || echo "    取得失敗"
    else
        echo -e "  ${YELLOW}○ オープンタスク: なし${NC}"
    fi
else
    echo -e "  ${RED}✗ タスク確認: Agent ID未設定のため不可${NC}"
fi

# ========================================
# 6. 最近の活動
# ========================================
echo -e "\n${YELLOW}🔍 最近の活動${NC}"

if [ ! -z "$CLAUDE_AGENT_ID" ]; then
    # Issue #99での最新コメント
    LATEST_COMMENT=$(gh issue view 99 --json comments --jq '.comments[-1] | "\(.createdAt) by \(.author.login)"' 2>/dev/null || echo "なし")
    echo -e "  ${BLUE}Issue #99 最新コメント: $LATEST_COMMENT${NC}"
fi

# ========================================
# 総合診断
# ========================================
echo -e "\n${YELLOW}🏥 総合診断${NC}"

HEALTH_SCORE=0
TOTAL_CHECKS=0

# スコア計算
[ "$ENV_OK" = true ] && ((HEALTH_SCORE++))
((TOTAL_CHECKS++))

pgrep -f "sleep 900" > /dev/null && ((HEALTH_SCORE++))
((TOTAL_CHECKS++))

gh auth status &>/dev/null && ((HEALTH_SCORE++))
((TOTAL_CHECKS++))

[ -d "/mnt/c/work/ITDO_ERP2" ] && ((HEALTH_SCORE++))
((TOTAL_CHECKS++))

# 診断結果
HEALTH_PERCENT=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))

if [ $HEALTH_PERCENT -ge 80 ]; then
    echo -e "  ${GREEN}✅ 健全性: $HEALTH_PERCENT% - 良好${NC}"
elif [ $HEALTH_PERCENT -ge 60 ]; then
    echo -e "  ${YELLOW}⚠️  健全性: $HEALTH_PERCENT% - 要注意${NC}"
else
    echo -e "  ${RED}❌ 健全性: $HEALTH_PERCENT% - 要対処${NC}"
fi

# ========================================
# 推奨事項
# ========================================
echo -e "\n${YELLOW}💡 推奨事項${NC}"

if [ "$ENV_OK" != true ]; then
    echo -e "  ${RED}• エージェントを初期化してください:${NC}"
    echo -e "    source scripts/claude-code-automation/agent/agent-init-v2.sh CC01"
fi

if ! pgrep -f "sleep 900" > /dev/null; then
    echo -e "  ${RED}• ポーリングプロセスを開始してください${NC}"
fi

if ! gh auth status &>/dev/null; then
    echo -e "  ${RED}• GitHub CLIにログインしてください:${NC}"
    echo -e "    gh auth login"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "