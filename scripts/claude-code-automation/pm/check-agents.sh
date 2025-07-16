#!/bin/bash
# PM用エージェント状況確認スクリプト
# WSL上の別端末から実行可能

# 色付け
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}                    Claude Code エージェント状況確認                                 ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 現在時刻
echo -e "\n${YELLOW}📅 確認時刻: $(date '+%Y-%m-%d %H:%M:%S %Z')${NC}"

# ========================================
# 1. エージェント別タスク状況
# ========================================
echo -e "\n${YELLOW}📋 エージェント別タスク状況${NC}"

for agent in cc01 cc02 cc03; do
    echo -e "\n${BLUE}【${agent^^}】${NC}"
    
    # オープンタスク数
    TASK_COUNT=$(gh issue list --label "$agent" --state open --json number | jq '. | length' 2>/dev/null || echo "0")
    echo -e "  オープンタスク: ${GREEN}$TASK_COUNT 件${NC}"
    
    # 最新タスク（上位3件）
    if [ "$TASK_COUNT" -gt 0 ]; then
        echo -e "  最新タスク:"
        gh issue list --label "$agent" --state open --limit 3 --json number,title,updatedAt --jq '.[] | "    #\(.number) \(.title) (更新: \(.updatedAt | fromdate | strftime("%m/%d %H:%M")))"' 2>/dev/null || echo "    取得失敗"
    fi
done

# ========================================
# 2. Issue #99 での最新活動
# ========================================
echo -e "\n${YELLOW}📊 Issue #99 での最新活動${NC}"

# 各エージェントの最終コメント時刻を取得
for agent in CC01 CC02 CC03; do
    LAST_COMMENT=$(gh issue view 99 --json comments --jq ".comments | map(select(.author.login == \"github-actions[bot]\" and (.body | contains(\"$agent\")))) | last | .createdAt" 2>/dev/null || echo "なし")
    
    if [ "$LAST_COMMENT" != "なし" ]; then
        # 時刻をフォーマット
        FORMATTED_TIME=$(date -d "$LAST_COMMENT" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$LAST_COMMENT")
        echo -e "  ${BLUE}$agent${NC}: $FORMATTED_TIME"
    else
        echo -e "  ${BLUE}$agent${NC}: ${RED}活動なし${NC}"
    fi
done

# ========================================
# 3. 重要PR状況
# ========================================
echo -e "\n${YELLOW}🔧 重要PR状況${NC}"

# PR #98の状況
PR_STATUS=$(gh pr view 98 --json state,title,statusCheckRollup --jq '{state: .state, title: .title, checks: (.statusCheckRollup | map(select(.status == "COMPLETED" and .conclusion == "FAILURE")) | length)}' 2>/dev/null)

if [ ! -z "$PR_STATUS" ]; then
    echo -e "\n${BLUE}PR #98 (CRITICAL)${NC}"
    echo "$PR_STATUS" | jq -r '"  状態: \(.state)\n  失敗チェック数: \(.checks)"'
fi

# ========================================
# 4. v2システム初期化状況
# ========================================
echo -e "\n${YELLOW}🔄 v2システム初期化状況${NC}"

# Issue #107のコメントをチェック
echo -e "\n${BLUE}Issue #107 (v2通知)への反応:${NC}"
RESPONSES=$(gh issue view 107 --json comments --jq '.comments | length' 2>/dev/null || echo "0")
echo -e "  総コメント数: $RESPONSES"

# CC02/CC03からの反応を探す
for agent in CC02 CC03; do
    HAS_RESPONSE=$(gh issue view 107 --json comments --jq ".comments | map(select(.body | contains(\"$agent\"))) | length" 2>/dev/null || echo "0")
    if [ "$HAS_RESPONSE" -gt "0" ]; then
        echo -e "  ${GREEN}$agent: 反応あり${NC}"
    else
        echo -e "  ${RED}$agent: 反応なし${NC}"
    fi
done

# ========================================
# 5. 推奨アクション
# ========================================
echo -e "\n${YELLOW}💡 推奨アクション${NC}"

# CC02/CC03が反応していない場合
if [ "$RESPONSES" -lt "3" ]; then
    echo -e "\n${RED}⚠️  CC02/CC03が v2システムに反応していません${NC}"
    echo -e "  以下のアクションを検討してください："
    echo -e "  1. 直接的な指示の再送信"
    echo -e "  2. 手動でのタスク実行"
    echo -e "  3. エージェントの再起動要請"
fi

# ========================================
# 6. WSLからの追加確認コマンド
# ========================================
echo -e "\n${YELLOW}🖥️  WSLから実行可能な追加確認${NC}"
echo -e "\n以下のコマンドで詳細確認が可能です："
echo ""
echo "# 1. エージェント健全性チェック（エージェント環境内で実行）"
echo "./scripts/claude-code-automation/agent/health-check.sh"
echo ""
echo "# 2. 特定エージェントのタスク詳細"
echo "gh issue list --label cc02 --state open --json number,title,body"
echo ""
echo "# 3. PR #98の最新状況"
echo "gh pr checks 98"
echo ""
echo "# 4. エージェントへの手動指示送信"
echo 'gh issue comment 107 --body "CC02/CC03: v2システムで初期化してください"'
echo ""

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"