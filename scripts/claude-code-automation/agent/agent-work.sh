#!/bin/bash
# Claude Code エージェント自動作業スクリプト

set -e

# エージェントID確認
AGENT_ID=${CLAUDE_AGENT_ID:-CC01}
AGENT_LABEL=$(echo $AGENT_ID | tr '[:upper:]' '[:lower:]')

# 色付け
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🤖 $AGENT_ID 自動作業実行${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. アクティブなタスクを取得
echo -e "\n${YELLOW}📋 タスク確認中...${NC}"
TASK_INFO=$(gh issue list --label "$AGENT_LABEL" --state open --limit 1 --json number,title,body)

if [ -z "$TASK_INFO" ] || [ "$TASK_INFO" = "[]" ]; then
    echo -e "${GREEN}✅ 現在処理すべきタスクはありません${NC}"
    exit 0
fi

# タスク情報を解析
TASK_NUMBER=$(echo "$TASK_INFO" | jq -r '.[0].number')
TASK_TITLE=$(echo "$TASK_INFO" | jq -r '.[0].title')
TASK_BODY=$(echo "$TASK_INFO" | jq -r '.[0].body')

echo -e "${GREEN}📌 タスク #$TASK_NUMBER: $TASK_TITLE${NC}"

# 2. 進捗報告
echo -e "\n${YELLOW}📢 進捗報告${NC}"
gh issue comment $TASK_NUMBER --body "🤖 **$AGENT_ID 自動作業開始**
- 開始時刻: $(date '+%Y-%m-%d %H:%M:%S')
- タスク解析中..."

# 3. タスクからコマンドを抽出
echo -e "\n${YELLOW}🔍 実行可能なコマンドを検索${NC}"
COMMANDS=$(echo "$TASK_BODY" | awk '/```bash/,/```/' | sed '1d;$d' | head -20)

if [ -z "$COMMANDS" ]; then
    echo -e "${YELLOW}⚠️  自動実行可能なコマンドが見つかりません${NC}"
    gh issue comment $TASK_NUMBER --body "⚠️ **$AGENT_ID**: 自動実行可能なコマンドが見つかりません。手動確認が必要です。"
    exit 0
fi

echo -e "${GREEN}📝 実行予定のコマンド:${NC}"
echo "$COMMANDS" | sed 's/^/  /'

# 4. 安全なコマンドのみ自動実行
SAFE_COMMANDS=$(echo "$COMMANDS" | grep -E "^(cd |git pull|git status|gh |make |pytest |npm test|uv run)" || true)

if [ -n "$SAFE_COMMANDS" ]; then
    echo -e "\n${YELLOW}🔧 安全なコマンドを実行中...${NC}"
    
    # 実行ログを記録
    EXEC_LOG=""
    
    while IFS= read -r cmd; do
        if [ -n "$cmd" ]; then
            echo -e "${BLUE}実行: $cmd${NC}"
            
            # コマンド実行と結果記録
            if OUTPUT=$(eval "$cmd" 2>&1); then
                echo -e "${GREEN}✓ 成功${NC}"
                EXEC_LOG+="✅ \`$cmd\` - 成功\n"
            else
                echo -e "${RED}✗ 失敗${NC}"
                EXEC_LOG+="❌ \`$cmd\` - 失敗\n"
                echo "$OUTPUT" | sed 's/^/  /'
            fi
        fi
    done <<< "$SAFE_COMMANDS"
    
    # 5. 実行結果を報告
    gh issue comment $TASK_NUMBER --body "🤖 **$AGENT_ID 自動実行完了**

**実行したコマンド:**
$EXEC_LOG

**次のステップ:**
- テスト結果の確認
- CI/CD状態の確認
- 必要に応じて手動介入

*自動実行時刻: $(date '+%Y-%m-%d %H:%M:%S')*"
    
else
    echo -e "${YELLOW}⚠️  安全に自動実行できるコマンドがありません${NC}"
    gh issue comment $TASK_NUMBER --body "⚠️ **$AGENT_ID**: コマンドの自動実行をスキップしました。手動での実行が必要です。"
fi

# 6. 追加の自動チェック
echo -e "\n${YELLOW}🔍 追加チェック${NC}"

# PR関連のタスクの場合
if echo "$TASK_TITLE" | grep -q "PR"; then
    PR_NUMBER=$(echo "$TASK_TITLE" | grep -oE '#[0-9]+' | tr -d '#' | head -1)
    if [ -n "$PR_NUMBER" ]; then
        echo "PR #$PR_NUMBER の状態確認..."
        PR_STATUS=$(gh pr view $PR_NUMBER --json statusCheckRollup --jq '.statusCheckRollup | map(select(.conclusion == "FAILURE")) | length' 2>/dev/null || echo "0")
        
        if [ "$PR_STATUS" -gt 0 ]; then
            echo -e "${RED}⚠️  PR #$PR_NUMBER に失敗しているチェックがあります${NC}"
            gh issue comment $TASK_NUMBER --body "⚠️ **CI/CD状態**: PR #$PR_NUMBER に $PR_STATUS 個の失敗したチェックがあります。"
        else
            echo -e "${GREEN}✅ PR #$PR_NUMBER のチェックは全て通過しています${NC}"
        fi
    fi
fi

echo -e "\n${GREEN}✅ 自動作業完了${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"