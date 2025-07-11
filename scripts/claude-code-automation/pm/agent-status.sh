#!/bin/bash
# Claude Code エージェントの状態確認スクリプト

set -e

# 色付け用の定数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                        Claude Code エージェント状態確認                         ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 現在日時
echo -e "\n📅 確認日時: $(date '+%Y-%m-%d %H:%M:%S')"

# アクティブなタスク
echo -e "\n${YELLOW}📋 アクティブなタスク${NC}"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────────────────────${NC}"

# 各エージェントのタスクを確認
for agent in cc01 cc02 cc03; do
    AGENT_UPPER=$(echo $agent | tr '[:lower:]' '[:upper:]')
    echo -e "\n${GREEN}▶ $AGENT_UPPER${NC}"
    
    # アクティブなIssueを取得
    ISSUES=$(gh issue list --label "$agent" --state open --json number,title,createdAt,labels --jq '.[] | "  #\(.number) - \(.title) (作成: \(.createdAt | split("T")[0]))"')
    
    if [ -z "$ISSUES" ]; then
        echo "  タスクなし"
    else
        echo "$ISSUES"
    fi
done

# 最近完了したタスク
echo -e "\n${YELLOW}✅ 最近完了したタスク（過去3日間）${NC}"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────────────────────${NC}"

THREE_DAYS_AGO=$(date -d "3 days ago" +%Y-%m-%d)
COMPLETED=$(gh issue list --label "claude-code-task" --state closed --search "closed:>$THREE_DAYS_AGO" --json number,title,closedAt,labels --jq '.[] | "  #\(.number) - \(.title) (完了: \(.closedAt | split("T")[0]))"')

if [ -z "$COMPLETED" ]; then
    echo "  最近の完了タスクなし"
else
    echo "$COMPLETED"
fi

# PRの状態
echo -e "\n${YELLOW}🔄 関連PR状態${NC}"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────────────────────${NC}"

# 主要PRの状態を確認
declare -A PR_ASSIGNMENTS=(
    ["98"]="CC01: Task-Department Integration"
    ["97"]="CC02: Role Service"
    ["95"]="CC03: E2E Tests"
)

for pr in 98 97 95; do
    if [ -n "${PR_ASSIGNMENTS[$pr]}" ]; then
        PR_INFO=$(gh pr view $pr --json state,statusCheckRollup 2>/dev/null || echo "NOTFOUND")
        
        if [ "$PR_INFO" != "NOTFOUND" ]; then
            STATE=$(echo $PR_INFO | jq -r '.state')
            CHECKS=$(echo $PR_INFO | jq -r '.statusCheckRollup | map(select(.conclusion == "FAILURE")) | length')
            
            if [ "$STATE" == "OPEN" ]; then
                if [ "$CHECKS" -eq 0 ]; then
                    STATUS="${GREEN}✓ All checks passing${NC}"
                else
                    STATUS="${RED}✗ $CHECKS checks failing${NC}"
                fi
                echo -e "  PR #$pr - ${PR_ASSIGNMENTS[$pr]}: $STATUS"
            fi
        fi
    fi
done

# サマリー統計
echo -e "\n${YELLOW}📊 サマリー${NC}"
echo -e "${YELLOW}────────────────────────────────────────────────────────────────────────────────${NC}"

OPEN_COUNT=$(gh issue list --label "claude-code-task" --state open --json number --jq 'length')
CLOSED_TODAY=$(gh issue list --label "claude-code-task" --state closed --search "closed:$(date +%Y-%m-%d)" --json number --jq 'length')

echo "  アクティブタスク: $OPEN_COUNT"
echo "  本日完了: $CLOSED_TODAY"

# 推奨アクション
if [ $OPEN_COUNT -eq 0 ]; then
    echo -e "\n${GREEN}💡 推奨: 新しいタスクを作成してください${NC}"
    echo "  実行: ./scripts/distribute-tasks.sh"
else
    echo -e "\n${BLUE}💡 各エージェントは割り当てられたタスクを確認してください${NC}"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"