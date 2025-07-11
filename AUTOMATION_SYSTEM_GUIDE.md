# 自動化システムの再起動・確認ガイド

## 🔄 自動化システムの再起動方法

### 1. 基本的な再起動（推奨）
```bash
# エージェントIDに合わせて実行
source scripts/claude-code-automation/agent/agent-init.sh CC01  # CC01の場合
source scripts/claude-code-automation/agent/agent-init.sh CC02  # CC02の場合
source scripts/claude-code-automation/agent/agent-init.sh CC03  # CC03の場合
```

### 2. 完全リセット後の再起動
```bash
# 1. 既存のバックグラウンドプロセスを停止
pkill -f "agent-work"
pkill -f "sleep 900"

# 2. 環境変数をリセット
unset CLAUDE_AGENT_ID
unset AGENT_LABEL

# 3. 作業ディレクトリへ移動
cd /mnt/c/work/ITDO_ERP2

# 4. 最新コードを取得
git pull origin main

# 5. 再初期化
source scripts/claude-code-automation/agent/agent-init.sh CC01  # エージェントIDに合わせて
```

## ✅ 自動化システムが稼働していることの確認方法

### 1. 初期化完了の確認
```bash
# プロンプトが変更されているか確認
echo $PS1  # 🤖 CC01 /mnt/c/work/ITDO_ERP2 $ のようになっているか

# エージェントIDが設定されているか確認
echo $CLAUDE_AGENT_ID  # CC01, CC02, CC03 のいずれかが表示されるか

# エイリアスが設定されているか確認
alias my-tasks  # コマンドが表示されるか
```

### 2. バックグラウンドプロセスの確認
```bash
# 自動ポーリングプロセスの確認
ps aux | grep "sleep 900"

# agent-work.shプロセスの確認
ps aux | grep agent-work

# jobsコマンドでバックグラウンドジョブ確認
jobs
```

### 3. タスク取得機能の確認
```bash
# 最新のタスクが取得できるか確認
my-tasks

# 具体的なラベル確認
gh issue list --label "cc01" --state open  # CC01の場合
```

### 4. 自動化の動作確認
```bash
# 手動で作業実行が可能か確認
./scripts/claude-code-automation/agent/agent-work.sh

# Issue #99での自動レポート確認
gh issue view 99 --comments | tail -10
```

## 🚨 問題がある場合の症状

### 初期化未完了の症状
- ❌ プロンプトが `🤖 CC01 /mnt/c/work/ITDO_ERP2 $` に変わっていない
- ❌ PIDが表示されていない
- ❌ `echo $CLAUDE_AGENT_ID` が空

### バックグラウンドプロセス停止の症状
- ❌ `ps aux | grep "sleep 900"` で何も見つからない
- ❌ `jobs` コマンドで何も表示されない
- ❌ 15分経過してもIssue #99に自動コメントがない

### タスク取得失敗の症状
- ❌ `my-tasks` コマンドが動作しない
- ❌ `gh issue list` でエラーが発生
- ❌ 最新のタスクが表示されない

## 🎯 成功している場合の証拠

### ✅ 初期化成功の証拠
```
🤖 CC01 /mnt/c/work/ITDO_ERP2 $ echo $CLAUDE_AGENT_ID
CC01

🤖 CC01 /mnt/c/work/ITDO_ERP2 $ my-tasks
#105: 🚨 CRITICAL: PR #98 needs 1-line whitespace fix - IMMEDIATE ACTION REQUIRED
#104: URGENT: Backend Integration Test Fixes for Multiple PRs
#103: Issue #103 - PR #98 Backend Test修正とマージ準備
```

### ✅ 自動ポーリング成功の証拠
```
🤖 CC01 /mnt/c/work/ITDO_ERP2 $ ps aux | grep "sleep 900"
user    12345  0.0  0.0   4276   764 pts/0    S    14:30   0:00 sleep 900
```

### ✅ 自動化機能成功の証拠
- Issue #99に定期的な自動コメントがある
- タスクの変更に自動的に反応している
- エイリアスが正しく動作している

## 💡 トラブルシューティング

### 問題: プロンプトが変わらない
```bash
# 解決方法: 手動でPS1を設定
PS1="🤖 CC01 \w $ "  # エージェントIDに合わせて変更
```

### 問題: バックグラウンドプロセスが起動しない
```bash
# 解決方法: 手動でポーリング開始
(
    while true; do
        sleep 900
        echo "[$(date '+%H:%M')] 定期タスクチェック"
        ./scripts/claude-code-automation/agent/agent-work.sh 2>/dev/null || true
    done
) &
```

### 問題: タスクが取得できない
```bash
# 解決方法: GitHub CLI認証確認
gh auth status
gh auth login  # 必要に応じて
```

## 🔧 緊急時の手動実行

自動化が動作しない場合でも、手動で作業を進められます：

```bash
# 1. 最新タスクの確認
gh issue list --label "cc01" --state open

# 2. 特定のタスクの詳細確認
gh issue view 105  # 最新の緊急タスク

# 3. 手動で作業実行
# 例: PR #98の1行修正
git checkout feature/task-department-integration-CRITICAL
sed -i '46s/.*//' backend/tests/conftest.py
git add backend/tests/conftest.py
git commit -m "fix: Remove whitespace from empty line in conftest.py"
git push origin feature/task-department-integration-CRITICAL
```

---

## 📝 Claude Code エージェント向けプロンプト集

### 🔄 自動化システム再起動プロンプト

#### 個別エージェント向け（CC01用）
```
🚨 緊急: 自動化システムの再起動をお願いします

以下のコマンドを順番に実行してください：

```bash
# 1. 既存プロセス停止
pkill -f "agent-work"
pkill -f "sleep 900"

# 2. 環境変数リセット
unset CLAUDE_AGENT_ID
unset AGENT_LABEL

# 3. 最新環境準備
cd /mnt/c/work/ITDO_ERP2
git pull origin main

# 4. 自動化システム再初期化
source scripts/claude-code-automation/agent/agent-init.sh CC01
```

✅ 成功確認：
```bash
echo $CLAUDE_AGENT_ID  # CC01が表示されるか
my-tasks               # 最新タスクが取得できるか
```

🎯 最優先タスク：`my-tasks`で確認してください
```

#### 統一プロンプト（全エージェント共通）
```
🚨 緊急: 自動化システムの再起動が必要です

以下のコマンドを順番に実行してください：

```bash
# 1. 既存プロセス停止
pkill -f "agent-work"
pkill -f "sleep 900"

# 2. 環境変数リセット
unset CLAUDE_AGENT_ID
unset AGENT_LABEL

# 3. 最新環境準備
cd /mnt/c/work/ITDO_ERP2
git pull origin main

# 4. 自動化システム再初期化（エージェントIDを適切に設定）
source scripts/claude-code-automation/agent/agent-init.sh CC01  # CC01の場合
source scripts/claude-code-automation/agent/agent-init.sh CC02  # CC02の場合
source scripts/claude-code-automation/agent/agent-init.sh CC03  # CC03の場合
```

✅ 成功確認：
```bash
echo $CLAUDE_AGENT_ID  # あなたのIDが表示されるか
my-tasks               # 最新タスクが取得できるか
```

🎯 最優先タスク：`my-tasks`で確認してください
```

### 💡 プロンプト使い分けガイド

#### 1. 個別対応プロンプト
- **使用場面**: 特定のエージェントに個別指示が必要な場合
- **メリット**: エージェントIDが明確、混乱しない
- **デメリット**: 複数エージェントへの送信が手間

#### 2. 統一プロンプト
- **使用場面**: 全エージェントに同じ作業を依頼する場合
- **メリット**: 効率的、一貫性がある
- **デメリット**: エージェントIDの設定を各自で判断する必要

#### 3. 緊急対応プロンプト
- **使用場面**: 迅速な対応が必要な場合
- **特徴**: 🚨マークで緊急性を強調
- **内容**: 最小限の手順で最大の効果

### 🎯 効果的なプロンプトの特徴

#### ✅ 良いプロンプトの要素
1. **明確な指示**: 実行すべきコマンドが明確
2. **順番付き**: 1, 2, 3...で手順が明確
3. **確認方法**: 成功/失敗の判定方法を提示
4. **緊急性表示**: 🚨マークで重要度を表現
5. **コードブロック**: ```bashで実行可能な形式

#### ❌ 避けるべきプロンプト
1. **曖昧な指示**: "適切に設定してください"
2. **長すぎる説明**: 重要な指示が埋もれる
3. **確認方法なし**: 成功したかわからない
4. **コマンドが不明確**: 実行できない形式

### 📊 プロンプト効果の測定

#### 成功指標
- **応答時間**: プロンプト送信から実行完了まで
- **実行成功率**: 指示通りに実行できた比率
- **エラー発生率**: 実行中のエラー発生頻度

#### 実績例（2025年7月11日）
- **CC01**: 1行修正プロンプト → 30秒で完了 ✅
- **CC02**: 自動化再起動プロンプト → 無反応 ❌
- **CC03**: 自動化再起動プロンプト → 無反応 ❌

### 🔧 プロンプト改善のポイント

#### 1. 応答性向上
- 緊急性の明確化（🚨マーク使用）
- 具体的な利益の提示
- 実行時間の短縮

#### 2. 理解しやすさ
- 技術的な背景説明の追加
- 視覚的な区切り（### マーク）
- 成功例の提示

#### 3. 実行可能性
- 環境依存部分の明確化
- エラー処理の追加
- 代替手段の提供

---

## 🎓 エージェント管理の知見

### 📈 効果的な管理戦略

#### 1. 定期的な状況確認
```bash
# 全エージェントの状況を一括確認
gh issue list --label "cc01,cc02,cc03" --state open
```

#### 2. 優先度の明確化
- **CRITICAL**: 🚨マーク、即座の対応が必要
- **HIGH**: 🎯マーク、当日中の対応が必要
- **MEDIUM**: 💡マーク、計画的な対応が必要

#### 3. 進捗の可視化
- Issue #99での定期報告
- PRの CI/CD 状況監視
- エージェントの応答時間追跡

### 🤝 エージェント間の連携促進

#### 1. 共通課題の共有
- Issue #104のような技術的問題共有
- 解決パターンの横展開
- 知見の蓄積

#### 2. 役割分担の明確化
- 主担当と副担当の設定
- 専門分野の活用
- 負荷分散

### 📚 学習事項

#### 成功パターン
1. **明確な指示**: 具体的なコマンド提示
2. **緊急性の表現**: 🚨マークの効果
3. **段階的アプローチ**: 基本→完全リセット
4. **確認方法の提示**: 成功/失敗の判定基準

#### 改善点
1. **応答性の向上**: 無反応エージェントへの対策
2. **自動化の信頼性**: バックグラウンドプロセスの安定性
3. **コミュニケーション**: エージェント間の情報共有

---

**重要**: 自動化システムは効率化のためのツールです。動作しない場合でも、手動で作業を進めることが可能です。

**追記**: このガイドは実際の運用経験に基づいて継続的に更新されます。新しい知見や改善点があれば追記してください。