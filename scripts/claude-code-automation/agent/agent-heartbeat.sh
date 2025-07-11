#!/bin/bash

# ========================================
# Claude Code Agent Heartbeat System
# ========================================
# エージェントの生存状態を定期的に報告する
# ハートビートシステム

# エージェントID確認
if [ -z "$CLAUDE_AGENT_ID" ]; then
    echo "❌ エラー: CLAUDE_AGENT_IDが設定されていません"
    exit 1
fi

# 設定
HEARTBEAT_DIR="/tmp/claude-agent-heartbeat"
HEARTBEAT_FILE="$HEARTBEAT_DIR/$CLAUDE_AGENT_ID.heartbeat"
HEARTBEAT_INTERVAL=60  # 60秒ごと
LOG_FILE="/tmp/claude-agent-$CLAUDE_AGENT_ID-heartbeat.log"

# ディレクトリ作成
mkdir -p "$HEARTBEAT_DIR"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ハートビート送信関数
send_heartbeat() {
    local status="$1"
    local current_task="$2"
    
    cat > "$HEARTBEAT_FILE" << EOF
{
  "agent_id": "$CLAUDE_AGENT_ID",
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "status": "$status",
  "current_task": "$current_task",
  "pid": $$,
  "uptime": "$(uptime -p)",
  "last_command": "$(history 1 2>/dev/null | sed 's/^[ ]*[0-9]*[ ]*//')"
}
EOF
    
    # GitHub Issueにも定期報告（15分ごと）
    if [ $(($(date +%s) % 900)) -lt 60 ]; then
        if command -v gh &> /dev/null; then
            local issue_number=$(gh issue list --label "$AGENT_LABEL" --state open --limit 1 --json number -q '.[0].number' 2>/dev/null)
            if [ -n "$issue_number" ]; then
                gh issue comment "$issue_number" --body "🤖 **$CLAUDE_AGENT_ID ハートビート**
- 状態: $status
- 現在のタスク: $current_task
- 最終更新: $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
            fi
        fi
    fi
}

# メイン処理
log "🚀 $CLAUDE_AGENT_ID ハートビートシステム起動"

# 初回ハートビート
send_heartbeat "active" "初期化中"

# バックグラウンドでハートビート送信
while true; do
    # 現在のタスク取得（簡易版）
    current_task="待機中"
    if [ -f "/tmp/claude-agent-$CLAUDE_AGENT_ID-current-task" ]; then
        current_task=$(cat "/tmp/claude-agent-$CLAUDE_AGENT_ID-current-task" 2>/dev/null || echo "不明")
    fi
    
    # プロセス状態確認
    if pgrep -f "claude" > /dev/null; then
        status="active"
    else
        status="idle"
    fi
    
    # ハートビート送信
    send_heartbeat "$status" "$current_task"
    
    # 待機
    sleep $HEARTBEAT_INTERVAL
done &

HEARTBEAT_PID=$!
echo $HEARTBEAT_PID > "/tmp/claude-agent-$CLAUDE_AGENT_ID-heartbeat.pid"

log "✅ ハートビートシステム開始 (PID: $HEARTBEAT_PID)"