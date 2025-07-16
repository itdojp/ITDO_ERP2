# 🔍 エージェント状態可視化システム改善

## 📋 概要
CC02/CC03の画面に新しい出力がなく、作業中か停止中か判別できない問題を解決するための改善案です。

## 🎯 実装した改善機能

### 1. ハートビートシステム (`agent-heartbeat.sh`)
- **機能**: エージェントが生きていることを定期的に報告
- **特徴**:
  - 60秒ごとにハートビートファイル更新
  - 現在のタスク状態を記録
  - 15分ごとにGitHub Issueにも報告（オプション）
  - バックグラウンドで自動実行

### 2. ステータスダッシュボード (`agent-status-dashboard.sh`)
- **機能**: 全エージェントの状態を一画面で監視
- **表示内容**:
  - 各エージェントの稼働状態（✅稼働中/⏸待機中/❌未起動）
  - 現在実行中のタスク
  - 割り当てられたIssue/PR数
  - CPU/メモリ使用率
  - 最終更新からの経過時間

### 3. タスク設定ユーティリティ (`set-current-task.sh`)
- **機能**: エージェントが何をしているか明示的に設定
- **使用例**:
  ```bash
  ./set-current-task.sh "Issue #103 - Backend Test修正中"
  ```

## 🚀 使用方法

### エージェント側での設定（CC01/CC02/CC03）

#### 1. 自動起動設定（~/.bashrcに追加）
```bash
# Claude Code Agent ハートビート自動起動
if [ -n "$CLAUDE_AGENT_ID" ] && [ -f "$WORK_DIR/scripts/claude-code-automation/agent/agent-heartbeat.sh" ]; then
    nohup $WORK_DIR/scripts/claude-code-automation/agent/agent-heartbeat.sh > /dev/null 2>&1 &
    echo "🤖 $CLAUDE_AGENT_ID ハートビートシステム起動"
fi

# タスク設定エイリアス
alias set-task='$WORK_DIR/scripts/claude-code-automation/agent/set-current-task.sh'
```

#### 2. 手動起動
```bash
# ハートビート開始
cd /home/work/ITDO_ERP2
./scripts/claude-code-automation/agent/agent-heartbeat.sh &

# タスク設定
./scripts/claude-code-automation/agent/set-current-task.sh "PR #98修正作業"
```

### 監視側での使用（PM/Ubuntu環境）

```bash
# ダッシュボード起動
cd /home/work/ITDO_ERP2
./scripts/claude-code-automation/monitor/agent-status-dashboard.sh
```

## 📊 期待される効果

1. **リアルタイム監視**
   - 5秒ごとに全エージェントの状態を更新
   - 2分以上更新がなければ「停止」と判定

2. **作業内容の可視化**
   - 各エージェントが何をしているか一目で分かる
   - アイドル状態と作業中を明確に区別

3. **リソース監視**
   - CPU/メモリ使用率でハング状態を検出
   - プロセスの有無を確認

## 🔧 追加改善案

### 1. Slackやメール通知
```bash
# エージェント停止時に通知
if [ "$status" = "stopped" ]; then
    curl -X POST -H 'Content-type: application/json' \
         --data '{"text":"⚠️ '$agent_id' が停止しました"}' \
         $SLACK_WEBHOOK_URL
fi
```

### 2. 作業ログの自動記録
```bash
# コマンド履歴を定期的に保存
history > "/tmp/claude-agent-$CLAUDE_AGENT_ID-history.log"
```

### 3. Web UIダッシュボード
- Flask/FastAPIで簡易Webサーバー構築
- ブラウザから状態監視
- グラフ表示で推移を可視化

## 📝 エージェント設定用コマンド

### CC01/CC02/CC03への設定指示
```bash
# ハートビートシステムの設定
echo '
# ハートビートシステム自動起動
if [ -n "$CLAUDE_AGENT_ID" ]; then
    if [ -f "/home/work/ITDO_ERP2/scripts/claude-code-automation/agent/agent-heartbeat.sh" ]; then
        nohup /home/work/ITDO_ERP2/scripts/claude-code-automation/agent/agent-heartbeat.sh > /dev/null 2>&1 &
        echo "🤖 $CLAUDE_AGENT_ID ハートビートシステム起動"
    fi
fi

# タスク設定エイリアス
alias set-task="/home/work/ITDO_ERP2/scripts/claude-code-automation/agent/set-current-task.sh"
' >> ~/.bashrc

source ~/.bashrc

# 動作確認
set-task "自動化システムテスト中"
```

## 🎯 導入優先度

1. **高優先度**: ハートビートシステム（最小限の可視化）
2. **中優先度**: ダッシュボード（統合監視）
3. **低優先度**: 通知システム（運用改善）

この改善により、エージェントの「無言の作業」問題が解決され、効率的な監視と管理が可能になります。