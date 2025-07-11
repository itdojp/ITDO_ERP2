#!/bin/bash

# ========================================
# Claude Code Agent Status Dashboard
# ========================================
# 全エージェントの状態を可視化する
# ダッシュボードシステム

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
HEARTBEAT_DIR="/tmp/claude-agent-heartbeat"
DASHBOARD_INTERVAL=5  # 5秒ごとに更新

# ヘッダー表示
show_header() {
    clear
    echo "================================================"
    echo "🤖 Claude Code Agent Status Dashboard"
    echo "================================================"
    echo "更新時刻: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================================"
    echo ""
}

# エージェント状態取得
get_agent_status() {
    local agent_id=$1
    local heartbeat_file="$HEARTBEAT_DIR/$agent_id.heartbeat"
    
    if [ -f "$heartbeat_file" ]; then
        # ハートビートファイルの更新時刻確認
        local last_update=$(stat -c %Y "$heartbeat_file" 2>/dev/null || stat -f %m "$heartbeat_file" 2>/dev/null)
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_update))
        
        # 2分以上更新がない場合は停止とみなす
        if [ $time_diff -gt 120 ]; then
            echo -e "${RED}⚠️  停止${NC} (最終更新: ${time_diff}秒前)"
        else
            # ハートビート内容読み取り
            local status=$(grep '"status"' "$heartbeat_file" | cut -d'"' -f4)
            local task=$(grep '"current_task"' "$heartbeat_file" | cut -d'"' -f4)
            
            if [ "$status" = "active" ]; then
                echo -e "${GREEN}✅ 稼働中${NC} - $task"
            else
                echo -e "${YELLOW}⏸  待機中${NC} - $task"
            fi
        fi
    else
        echo -e "${RED}❌ 未起動${NC}"
    fi
}

# GitHub Issue状態取得
get_issue_status() {
    local agent_label=$1
    
    if command -v gh &> /dev/null; then
        local issue_count=$(gh issue list --label "$agent_label" --state open --json number -q '. | length' 2>/dev/null || echo "0")
        local pr_count=$(gh pr list --label "$agent_label" --state open --json number -q '. | length' 2>/dev/null || echo "0")
        
        echo "Issues: $issue_count | PRs: $pr_count"
    else
        echo "GitHub CLI未設定"
    fi
}

# プロセス情報取得
get_process_info() {
    local agent_id=$1
    local agent_label=$(echo $agent_id | tr '[:upper:]' '[:lower:]')
    
    # Claude プロセス確認
    local claude_pids=$(pgrep -f "claude.*$agent_label" 2>/dev/null)
    if [ -n "$claude_pids" ]; then
        local cpu_usage=$(ps aux | grep -E "claude.*$agent_label" | grep -v grep | awk '{print $3}' | head -1)
        local mem_usage=$(ps aux | grep -E "claude.*$agent_label" | grep -v grep | awk '{print $4}' | head -1)
        echo "CPU: ${cpu_usage}% | MEM: ${mem_usage}%"
    else
        echo "プロセスなし"
    fi
}

# メインループ
while true; do
    show_header
    
    # 各エージェントの状態表示
    for agent_id in CC01 CC02 CC03; do
        agent_label=$(echo $agent_id | tr '[:upper:]' '[:lower:]')
        
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${BLUE}🤖 $agent_id${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        echo -n "状態: "
        get_agent_status "$agent_id"
        
        echo -n "タスク: "
        get_issue_status "$agent_label"
        
        echo -n "リソース: "
        get_process_info "$agent_id"
        
        echo ""
    done
    
    # 統計情報
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 統計情報"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # アクティブエージェント数
    active_count=0
    for agent_id in CC01 CC02 CC03; do
        if [ -f "$HEARTBEAT_DIR/$agent_id.heartbeat" ]; then
            last_update=$(stat -c %Y "$HEARTBEAT_DIR/$agent_id.heartbeat" 2>/dev/null || stat -f %m "$HEARTBEAT_DIR/$agent_id.heartbeat" 2>/dev/null)
            current_time=$(date +%s)
            if [ $((current_time - last_update)) -lt 120 ]; then
                ((active_count++))
            fi
        fi
    done
    
    echo "稼働中エージェント: $active_count / 3"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "更新間隔: ${DASHBOARD_INTERVAL}秒 | 終了: Ctrl+C"
    
    sleep $DASHBOARD_INTERVAL
done