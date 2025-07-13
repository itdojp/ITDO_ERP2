#!/bin/bash
# 超簡単初期化スクリプト - 失敗しようがないレベル

echo "======================================"
echo "超簡単 Claude Code 初期化"
echo "======================================"
echo ""
echo "あなたのエージェントIDを入力してください："
echo "CC01, CC02, CC03 のいずれか"
read -p "ID: " AGENT_ID

echo ""
echo "設定中..."
export CLAUDE_AGENT_ID=$AGENT_ID
echo "CLAUDE_AGENT_ID=$AGENT_ID" >> ~/.bashrc

echo ""
echo "✅ 完了！"
echo ""
echo "確認："
echo "あなたのID: $CLAUDE_AGENT_ID"
echo ""
echo "タスク確認コマンド："
echo "gh issue list --label '$AGENT_ID' --state open"
echo ""
echo "======================================"