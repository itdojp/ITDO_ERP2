#!/bin/bash
# Claude Code エージェント クイックスタート
# 最速で作業を開始するためのワンライナー集

AGENT_ID=${1:-CC01}

echo "🚀 Claude Code $AGENT_ID クイックスタート"
echo ""
echo "以下のコマンドをコピー＆ペーストして実行してください："
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# 1️⃣ 最速初期化（1行）"
echo "cd /mnt/c/work/ITDO_ERP2 && git pull origin main && source scripts/claude-code-automation/agent/agent-init-v2.sh $AGENT_ID"
echo ""
echo "# 2️⃣ タスク確認と実行（初期化後）"
echo "my-tasks && ./scripts/claude-code-automation/agent/agent-work.sh"
echo ""
echo "# 3️⃣ 健全性チェック"
echo "./scripts/claude-code-automation/agent/health-check.sh"
echo ""
echo "# 4️⃣ 問題がある場合のリセット"
echo "pkill -f 'agent-work' && pkill -f 'sleep 900' && unset CLAUDE_AGENT_ID && cd /mnt/c/work/ITDO_ERP2 && source scripts/claude-code-automation/agent/agent-init-v2.sh $AGENT_ID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 ヒント:"
echo "  - 上記の 1️⃣ を実行するだけで作業開始できます"
echo "  - 問題がある場合は 4️⃣ でリセット"
echo "  - 詳細は AUTOMATION_SYSTEM_GUIDE.md 参照"
echo ""