#!/bin/bash
# Claude Code エージェントへのタスク配布スクリプト

set -e

# 色付け用の定数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Claude Code Task Distribution ===${NC}"

# 日付とタイムスタンプ
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# タスクタイプの選択
echo -e "\n${YELLOW}タスクタイプを選択してください:${NC}"
echo "1) 個別タスク（各エージェントに異なるタスク）"
echo "2) 共通タスク（全エージェントに同じタスク）"
echo "3) カスタムタスク（対話的に入力）"
read -p "選択 [1-3]: " TASK_TYPE

# 共通指示の入力
echo -e "\n${YELLOW}共通指示を入力してください（Enterで終了）:${NC}"
COMMON_INSTRUCTION=""
while IFS= read -r line; do
    [[ -z "$line" ]] && break
    COMMON_INSTRUCTION+="$line\n"
done

# タスクタイプに応じた処理
case $TASK_TYPE in
    1)
        # 個別タスク
        echo -e "\n${GREEN}個別タスクを作成します${NC}"
        
        # CC01
        gh issue create \
            --title "【CC01】$DATE - PR #98 Task-Department Integration修正" \
            --label "claude-code-task,cc01" \
            --body "$(cat <<EOF
## 📋 タスク概要
PR #98 (Task-Department Integration) のCI/CD修正を完了させる

## 🎯 本日の目標
1. backend-test失敗の修正
2. 全テスト通過確認
3. CI/CDグリーン達成

## 📝 共通指示
$COMMON_INSTRUCTION

## ✅ 完了条件
- [ ] Backend tests: 全て通過
- [ ] CI/CD: 全てグリーン
- [ ] PR: Ready for review

## 🔧 推奨手順
\`\`\`bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/task-department-integration-CRITICAL
git pull origin main --rebase
cd backend && uv run pytest tests/integration/ -v
\`\`\`

## 📊 進捗報告
完了したらこのIssueにコメントしてください。
EOF
        )"
        
        # CC02
        gh issue create \
            --title "【CC02】$DATE - PR #97 Role Service修正" \
            --label "claude-code-task,cc02" \
            --body "$(cat <<EOF
## 📋 タスク概要
PR #97 (Role Service & Permission Matrix) のCore Foundation Tests修正

## 🎯 本日の目標
1. Core Foundation Tests失敗の解決
2. SQLAlchemy外部キー参照エラー修正
3. Backend tests通過

## 📝 共通指示
$COMMON_INSTRUCTION

## ✅ 完了条件
- [ ] Core Foundation Tests: 通過
- [ ] Backend tests: 通過
- [ ] Ruff: エラーなし

## 🔧 推奨手順
\`\`\`bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/role-service
git pull origin main --rebase
cd backend && uv run pytest tests/unit/test_models.py -v
\`\`\`

## 📊 進捗報告
完了したらこのIssueにコメントしてください。
EOF
        )"
        
        # CC03
        gh issue create \
            --title "【CC03】$DATE - PR #95 E2E Tests環境修正" \
            --label "claude-code-task,cc03" \
            --body "$(cat <<EOF
## 📋 タスク概要
PR #95 (E2E Testing Infrastructure) の環境設定修正

## 🎯 本日の目標
1. E2E test環境の設定修正
2. Playwright基本テスト実装
3. CI/CD統合確認

## 📝 共通指示
$COMMON_INSTRUCTION

## ✅ 完了条件
- [ ] E2E tests: 基本テスト通過
- [ ] CI/CD: E2Eステップ成功
- [ ] ドキュメント: 更新完了

## 🔧 推奨手順
\`\`\`bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/e2e-test-implementation
git pull origin main --rebase
cd frontend && npm run test:e2e
\`\`\`

## 📊 進捗報告
完了したらこのIssueにコメントしてください。
EOF
        )"
        ;;
        
    2)
        # 共通タスク
        echo -e "\n${YELLOW}共通タスクの内容を入力してください:${NC}"
        read -p "タスク概要: " TASK_SUMMARY
        
        for agent in CC01 CC02 CC03; do
            gh issue create \
                --title "【$agent】$DATE - $TASK_SUMMARY" \
                --label "claude-code-task,${agent,,}" \
                --body "$(cat <<EOF
## 📋 タスク概要
$TASK_SUMMARY

## 📝 共通指示
$COMMON_INSTRUCTION

## ✅ 完了条件
- [ ] タスク完了
- [ ] テスト通過
- [ ] ドキュメント更新

## 📊 進捗報告
完了したらこのIssueにコメントしてください。
EOF
            )"
        done
        ;;
        
    3)
        # カスタムタスク
        echo -e "\n${YELLOW}カスタムタスクを作成します${NC}"
        
        for agent in CC01 CC02 CC03; do
            echo -e "\n${GREEN}$agent のタスク:${NC}"
            read -p "タイトル: " TITLE
            read -p "概要: " SUMMARY
            
            gh issue create \
                --title "【$agent】$DATE - $TITLE" \
                --label "claude-code-task,${agent,,}" \
                --body "$(cat <<EOF
## 📋 タスク概要
$SUMMARY

## 📝 共通指示
$COMMON_INSTRUCTION

## ✅ 完了条件
- [ ] タスク完了
- [ ] テスト通過
- [ ] レビュー準備完了

## 📊 進捗報告
完了したらこのIssueにコメントしてください。
EOF
            )"
        done
        ;;
esac

echo -e "\n${GREEN}✅ タスク配布完了！${NC}"
echo -e "\n${YELLOW}作成されたタスクを確認:${NC}"
gh issue list --label "claude-code-task" --state open --limit 3

echo -e "\n${YELLOW}各エージェントで以下のコマンドを実行してタスクを確認してください:${NC}"
echo "CC01: gh issue list --label 'cc01' --state open"
echo "CC02: gh issue list --label 'cc02' --state open"
echo "CC03: gh issue list --label 'cc03' --state open"