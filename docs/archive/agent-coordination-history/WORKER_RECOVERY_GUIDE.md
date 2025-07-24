# ワーカー復旧ガイド

## 📋 現在の状況

ワーカーがプロンプト入力画面に戻っている状態は **正常** です。

## ✅ 問題ない理由

1. **自動化ツール設計の意図**
   - エージェントは自動ポーリング（15分間隔）で動作
   - プロンプト画面で待機しながらバックグラウンドで自動実行

2. **バックグラウンド処理**
   - 初期化時に自動ポーリングが開始
   - PIDが表示されてバックグラウンドで継続実行
   - 15分ごとに`agent-work.sh`が自動実行

## 🔍 状態確認方法

### 1. バックグラウンド処理の確認
```bash
# 実行中プロセスを確認
ps aux | grep agent-work

# または、jobsコマンドで確認
jobs

# 具体的なポーリング状況
ps aux | grep "sleep 900"
```

### 2. 自動化が動作しているかの確認
```bash
# 最新のタスクコメントを確認
gh issue view 99 --comments

# エージェントの状態確認
./scripts/claude-code-automation/pm/agent-status.sh
```

## 🚨 問題がある場合の症状

以下の場合は再開が必要：

1. **初期化が完了していない**
   - プロンプトがまだ `🤖 CC01 /mnt/c/work/ITDO_ERP2 $` に変わっていない
   - PIDが表示されていない

2. **エラーで停止**
   - バックグラウンドプロセスが見つからない
   - Issue #99にエラーコメントがある

3. **長時間無反応**
   - 15分以上経過してもIssueにコメントがない

## 🔧 再開・復旧方法

### 方法1: 通常の再開
```bash
# 1. 作業ディレクトリ確認
cd /mnt/c/work/ITDO_ERP2

# 2. 最新コード取得
git pull origin main

# 3. 再初期化（IDに合わせて）
source scripts/claude-code-automation/agent/agent-init.sh CC01  # CC01の場合
```

### 方法2: 強制リセット
```bash
# 1. 既存のバックグラウンドプロセスを停止
pkill -f "agent-work"
pkill -f "sleep 900"

# 2. 環境変数リセット
unset CLAUDE_AGENT_ID
unset AGENT_LABEL

# 3. 再初期化
cd /mnt/c/work/ITDO_ERP2
git pull origin main
source scripts/claude-code-automation/agent/agent-init.sh CC01
```

### 方法3: 手動実行（緊急時）
```bash
# 自動化を無効にして手動実行
export CLAUDE_NO_AUTO_POLLING=1
source scripts/claude-code-automation/agent/agent-init.sh CC01

# 手動でタスク実行
./scripts/claude-code-automation/agent/agent-work.sh
```

## 📊 正常な動作の確認項目

### 初期化完了の証拠
- ✅ プロンプトが変更されている
- ✅ PIDが表示されている
- ✅ 「自動ポーリング開始」メッセージ
- ✅ エイリアスが設定されている

### 継続動作の証拠
- ✅ `ps aux | grep agent-work` でプロセス確認
- ✅ Issue #99に定期的なコメント
- ✅ `my-tasks`コマンドが機能

## 💡 推奨対応

### 1. まずは状態確認
```bash
# エージェントIDが設定されているか確認
echo $CLAUDE_AGENT_ID

# タスクが見えるか確認
my-tasks || gh issue list --label "cc01" --state open
```

### 2. 問題なければそのまま継続
- プロンプト画面で待機は正常
- 15分ごとに自動実行される
- 手動実行も可能

### 3. 異常があれば再初期化
```bash
source scripts/claude-code-automation/agent/agent-init.sh [あなたのID]
```

## 🎯 ベストプラクティス

1. **セッション開始時は必ず初期化**
2. **プロンプト変更を確認**
3. **PID表示を確認**
4. **15分後にIssueコメントを確認**

---

**結論: プロンプト入力画面への復帰は正常な動作です。自動化がバックグラウンドで継続しています。**