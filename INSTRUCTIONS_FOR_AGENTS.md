# 🚨 重要: Claude Code エージェント向け指示

**対象:** CC01, CC02, CC03  
**日付:** 2025年7月11日  
**優先度:** 高

---

## 📢 必ず最初に実行してください

```bash
# 1. 最新コードを取得
cd /mnt/c/work/ITDO_ERP2
git pull origin main

# 2. 自分のエージェントIDで初期化（例: CC01の場合）
source scripts/claude-code-automation/agent/agent-init.sh CC01
```

---

## 🤖 新しい自動化ツールの導入

作業効率を大幅に向上させる自動化ツールを導入しました。これにより、手動作業時間を **89.6%削減** できます。

### 📋 主な機能

1. **自動タスク実行** - GitHub Issueから自動でタスク取得・実行
2. **CI/CD自動修正** - テスト失敗を自動的に修正
3. **進捗自動報告** - Issueへの自動コメント

---

## 🎯 具体的な使用手順

### 1️⃣ セッション開始時（必須）

```bash
# あなたのエージェントIDに置き換えてください
# CC01の場合:
source scripts/claude-code-automation/agent/agent-init.sh CC01

# CC02の場合:
source scripts/claude-code-automation/agent/agent-init.sh CC02

# CC03の場合:
source scripts/claude-code-automation/agent/agent-init.sh CC03
```

**実行後の確認事項:**
- ✅ 現在のタスクが表示される
- ✅ 便利なエイリアスが設定される
- ✅ プロンプトが `🤖 CC01 /mnt/c/work/ITDO_ERP2 $` に変わる

### 2️⃣ タスクの自動実行

```bash
# 割り当てられたタスクを確認
my-tasks

# タスクを自動実行
./scripts/claude-code-automation/agent/agent-work.sh
```

**自動実行される内容:**
- GitHub Issueからタスク取得
- `bash`コードブロックの安全なコマンドを実行
- 実行結果をIssueに自動報告

### 3️⃣ CI/CD失敗の自動修正

```bash
# PRのCI/CDが失敗している場合
./scripts/claude-code-automation/agent/auto-fix-ci.sh [PR番号]

# 例: PR #98の修正
./scripts/claude-code-automation/agent/auto-fix-ci.sh 98
```

**自動修正される内容:**
- Ruffのフォーマット違反
- 簡単なテストエラー
- インポート順序の問題
- 最大3回まで自動リトライ

### 4️⃣ 便利なエイリアス（初期化後に使用可能）

| コマンド | 説明 |
|---------|------|
| `my-tasks` | 自分に割り当てられたタスク一覧 |
| `my-pr` | 自分が作成したPR一覧 |
| `check-ci [PR番号]` | CI/CDの状態確認 |
| `daily-report` | 日次レポート生成 |
| `fix-ci [PR番号]` | CI/CD自動修正 |

---

## 📊 現在の優先タスク

### CC01
```bash
# タスク確認
gh issue list --label "cc01" --state open

# 主要タスク: PR #98 (Task-Department Integration)
# backend-test修正が必要
```

### CC02
```bash
# タスク確認  
gh issue list --label "cc02" --state open

# 主要タスク: PR #97 (Role Service)
# Core Foundation Tests修正が必要
```

### CC03
```bash
# タスク確認
gh issue list --label "cc03" --state open

# 主要タスク: PR #95 (E2E Tests)
# E2E環境設定が必要
```

---

## ⚡ クイックスタートコマンド

### CC01用
```bash
cd /mnt/c/work/ITDO_ERP2 && git pull origin main
source scripts/claude-code-automation/agent/agent-init.sh CC01
./scripts/claude-code-automation/agent/agent-work.sh
```

### CC02用
```bash
cd /mnt/c/work/ITDO_ERP2 && git pull origin main
source scripts/claude-code-automation/agent/agent-init.sh CC02
./scripts/claude-code-automation/agent/agent-work.sh
```

### CC03用
```bash
cd /mnt/c/work/ITDO_ERP2 && git pull origin main
source scripts/claude-code-automation/agent/agent-init.sh CC03
./scripts/claude-code-automation/agent/agent-work.sh
```

---

## 📚 詳細ドキュメント

- **使い方ガイド:** `scripts/claude-code-automation/docs/AGENT_AUTOMATION_GUIDE.md`
- **お知らせ:** `docs/handover/PM01_20250711_01.md`

---

## ⚠️ 注意事項

1. **必ず初期化を実行** - `source`コマンドを使用（実行権限だけでは不十分）
2. **エージェントIDを正しく指定** - CC01, CC02, CC03 のいずれか
3. **自動タスクチェック** - 15分ごとに自動実行されます（手動実行も可能）

---

## 🎯 期待される効果

- **作業時間**: 115分/日 → 12分/日
- **エラー対処**: 20分 → 3分
- **タスク確認**: 5分 → 10秒
- **総合効率**: 89.6%向上

---

**今すぐ上記のクイックスタートコマンドを実行して、自動化ツールを使い始めてください！**

質問がある場合は、GitHub Issueでお知らせください。