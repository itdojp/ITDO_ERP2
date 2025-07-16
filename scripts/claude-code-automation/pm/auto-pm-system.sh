#!/bin/bash

# ========================================
# Claude Code Auto PM System
# ========================================
# 自動プロジェクト管理システム
# 目標を与えると自動で指示・監視・修正を行う

# 設定
PM_CONFIG_DIR="$HOME/.claude-pm"
GOAL_FILE="$PM_CONFIG_DIR/current-goal.json"
TASK_QUEUE="$PM_CONFIG_DIR/task-queue.json"
PM_LOG="$PM_CONFIG_DIR/pm-system.log"

# ディレクトリ作成
mkdir -p "$PM_CONFIG_DIR"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$PM_LOG"
}

# 目標設定関数
set_goal() {
    local goal_title="$1"
    local goal_description="$2"
    local deadline="$3"
    
    cat > "$GOAL_FILE" << EOF
{
  "title": "$goal_title",
  "description": "$goal_description",
  "deadline": "$deadline",
  "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "status": "active",
  "tasks": []
}
EOF
    
    log "🎯 新しい目標を設定: $goal_title"
}

# タスク分解関数
decompose_tasks() {
    local goal_title=$(jq -r '.title' "$GOAL_FILE")
    
    # GitHubにメタIssueを作成
    local meta_issue_url=$(gh issue create \
        --title "🎯 [META] $goal_title" \
        --body "$(cat << EOF
## 目標
$goal_title

## タスク分解
この目標を達成するために以下のタスクに分解します：

### Phase 1: 準備
- [ ] 現状分析
- [ ] 要件定義
- [ ] 技術調査

### Phase 2: 実装
- [ ] コア機能実装
- [ ] テスト作成
- [ ] ドキュメント作成

### Phase 3: 完成
- [ ] 統合テスト
- [ ] パフォーマンス最適化
- [ ] デプロイ準備

## 自動管理
このIssueはPM自動化システムによって管理されます。
EOF
)" \
        --label "meta,pm-system")
    
    log "📋 メタIssue作成: $meta_issue_url"
}

# エージェント割当関数
assign_agent() {
    local task_title="$1"
    local agent_id="$2"
    local priority="$3"
    
    # エージェントのワークロード確認
    local agent_label=$(echo $agent_id | tr '[:upper:]' '[:lower:]')
    local current_tasks=$(gh issue list --label "$agent_label" --state open --json number -q '. | length')
    
    if [ "$current_tasks" -lt 3 ]; then
        # タスクIssue作成
        local issue_url=$(gh issue create \
            --title "[$agent_id] $task_title" \
            --body "$(cat << EOF
## タスク概要
$task_title

## 優先度
$priority

## 期限
$(date -d '+2 days' '+%Y-%m-%d')

## 自動管理
このタスクはPM自動化システムによって管理されます。
進捗は定期的に確認され、必要に応じて支援が提供されます。

---
🤖 Auto-assigned by PM System
EOF
)" \
            --label "$agent_label,pm-system,$priority")
        
        log "✅ $agent_id にタスク割当: $task_title"
        echo "$issue_url"
    else
        log "⚠️  $agent_id は既に $current_tasks タスクを担当中"
        echo ""
    fi
}

# 進捗監視関数
monitor_progress() {
    log "📊 進捗監視開始..."
    
    # 各エージェントの状態確認
    for agent_id in CC01 CC02 CC03; do
        agent_label=$(echo $agent_id | tr '[:upper:]' '[:lower:]')
        
        # アクティブなタスク取得
        local active_issues=$(gh issue list \
            --label "$agent_label,pm-system" \
            --state open \
            --json number,title,updatedAt \
            --jq '.[] | "\(.number):\(.title):\(.updatedAt)"')
        
        while IFS=: read -r issue_num issue_title updated_at; do
            if [ -n "$issue_num" ]; then
                # 最終更新からの経過時間確認
                local update_timestamp=$(date -d "$updated_at" +%s)
                local current_timestamp=$(date +%s)
                local hours_since_update=$(( (current_timestamp - update_timestamp) / 3600 ))
                
                if [ "$hours_since_update" -gt 12 ]; then
                    # 12時間以上更新がない場合はリマインダー
                    send_reminder "$agent_id" "$issue_num" "$issue_title"
                fi
                
                # 進捗確認
                check_task_progress "$issue_num"
            fi
        done <<< "$active_issues"
    done
}

# リマインダー送信関数
send_reminder() {
    local agent_id="$1"
    local issue_num="$2"
    local issue_title="$3"
    
    gh issue comment "$issue_num" --body "$(cat << EOF
## 📢 進捗確認

$agent_id さん、このタスクの進捗はいかがでしょうか？

12時間以上更新がないようです。以下の点を確認してください：

1. **現在の状況**: 作業は進んでいますか？
2. **ブロッカー**: 何か問題が発生していますか？
3. **必要な支援**: サポートが必要ですか？

状況を教えていただければ、適切な支援を提供します。

---
🤖 PM自動化システムからの確認
EOF
)"
    
    log "📮 $agent_id にリマインダー送信 (Issue #$issue_num)"
}

# タスク進捗確認関数
check_task_progress() {
    local issue_num="$1"
    
    # PR関連確認
    local linked_prs=$(gh issue view "$issue_num" --json linkedPullRequests -q '.linkedPullRequests[] | .number')
    
    if [ -n "$linked_prs" ]; then
        for pr_num in $linked_prs; do
            # PRのCI状態確認
            local ci_status=$(gh pr checks "$pr_num" --json state -q '.[].state' | grep -c "FAILURE")
            
            if [ "$ci_status" -gt 0 ]; then
                # CI失敗の場合は支援提供
                provide_ci_support "$issue_num" "$pr_num"
            fi
        done
    fi
}

# CI支援提供関数
provide_ci_support() {
    local issue_num="$1"
    local pr_num="$2"
    
    # 失敗しているチェックの詳細取得
    local failed_checks=$(gh pr checks "$pr_num" \
        --json name,conclusion,detailsUrl \
        --jq '.[] | select(.conclusion=="FAILURE") | "\(.name): \(.detailsUrl)"')
    
    gh issue comment "$issue_num" --body "$(cat << EOF
## 🔧 CI失敗の自動支援

PR #$pr_num でCI失敗を検出しました。

### 失敗しているチェック
$failed_checks

### 推奨アクション
1. エラーログを確認
2. ローカルでテスト実行
3. 必要に応じて修正をプッシュ

### よくある原因と対策
- **型エラー**: \`npm run typecheck\` でローカル確認
- **テスト失敗**: \`npm test\` または \`uv run pytest\`
- **Lint違反**: \`npm run lint:fix\` または \`ruff format\`

---
🤖 PM自動化システムによる支援
EOF
)"
    
    log "🔧 Issue #$issue_num に CI支援を提供"
}

# メイン実行ループ
main_loop() {
    log "🚀 PM自動化システム起動"
    
    while true; do
        # 現在の目標確認
        if [ -f "$GOAL_FILE" ]; then
            local goal_status=$(jq -r '.status' "$GOAL_FILE")
            
            if [ "$goal_status" = "active" ]; then
                # 進捗監視
                monitor_progress
                
                # 新規タスクの割当
                allocate_new_tasks
                
                # 完了確認
                check_goal_completion
            fi
        fi
        
        # 30分待機
        sleep 1800
    done
}

# コマンドライン処理
case "$1" in
    "set-goal")
        set_goal "$2" "$3" "$4"
        decompose_tasks
        ;;
    "monitor")
        monitor_progress
        ;;
    "start")
        main_loop
        ;;
    *)
        echo "使用方法:"
        echo "  $0 set-goal <タイトル> <説明> <期限>"
        echo "  $0 monitor    # 手動で進捗確認"
        echo "  $0 start      # 自動監視開始"
        ;;
esac