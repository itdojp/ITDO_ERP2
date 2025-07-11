#!/bin/bash

# ========================================
# Claude Code Agent Current Task Setter
# ========================================
# エージェントの現在のタスクを設定する
# ユーティリティスクリプト

# 使用方法確認
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <タスク説明>"
    echo "例: $0 'Issue #103 - PR #98 Backend Test修正中'"
    exit 1
fi

# エージェントID確認
if [ -z "$CLAUDE_AGENT_ID" ]; then
    echo "❌ エラー: CLAUDE_AGENT_IDが設定されていません"
    exit 1
fi

# タスク設定
TASK_DESCRIPTION="$*"
TASK_FILE="/tmp/claude-agent-$CLAUDE_AGENT_ID-current-task"

# タスクファイルに書き込み
echo "$TASK_DESCRIPTION" > "$TASK_FILE"

# 確認メッセージ
echo "✅ $CLAUDE_AGENT_ID の現在のタスクを設定しました:"
echo "   $TASK_DESCRIPTION"

# ハートビートプロセスに通知（もし動作していれば）
if [ -f "/tmp/claude-agent-$CLAUDE_AGENT_ID-heartbeat.pid" ]; then
    HEARTBEAT_PID=$(cat "/tmp/claude-agent-$CLAUDE_AGENT_ID-heartbeat.pid")
    if kill -0 $HEARTBEAT_PID 2>/dev/null; then
        echo "📡 ハートビートシステムに通知しました"
    fi
fi