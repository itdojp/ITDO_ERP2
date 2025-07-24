# 🧪 自動化システム段階的テスト計画

## 目的
CC02/CC03で自動化システムの効果を検証し、問題点を特定する

## 📋 段階的テストプラン

### 🟢 Phase 1: 最小限の動作確認（5分）
```bash
# 1. 環境変数設定のみ
export CLAUDE_AGENT_ID=CC02
echo $CLAUDE_AGENT_ID

# 2. エイリアス設定のみ  
alias my-tasks="gh issue list --label cc02 --state open"
my-tasks
```
**確認事項**: 基本的なコマンドが動作するか

### 🟡 Phase 2: 手動で主要機能テスト（10分）
```bash
# 1. 作業ディレクトリ移動
cd /mnt/c/work/ITDO_ERP2

# 2. タスク確認（手動）
gh issue list --label "cc02" --state open

# 3. agent-work.sh の内容確認（実行せず）
cat scripts/claude-code-automation/agent/agent-work.sh
```
**確認事項**: スクリプトの内容理解、手動実行の可否

### 🟠 Phase 3: 初期化スクリプト実行（15分）
```bash
# 1. 最新コード取得
git pull origin main

# 2. v2初期化実行
source scripts/claude-code-automation/agent/agent-init-v2.sh CC02

# 3. 健全性チェック
./scripts/claude-code-automation/agent/health-check.sh
```
**確認事項**: 
- 初期化成功/失敗
- エラーメッセージ
- プロセス起動状況

### 🔴 Phase 4: 自動化機能フル活用（20分）
```bash
# 1. 自動タスク実行
./scripts/claude-code-automation/agent/agent-work.sh

# 2. バックグラウンドプロセス確認
ps aux | grep "sleep 900"

# 3. 15分待機して自動実行確認
# （または手動で再実行）
```
**確認事項**: 自動化の完全動作

## 🔍 各段階での確認ポイント

### 技術的確認
1. **権限問題**: ファイルアクセス、実行権限
2. **環境問題**: パス、環境変数
3. **認証問題**: GitHub CLI
4. **プロセス問題**: バックグラウンド実行

### 運用的確認
1. **理解度**: 各コマンドの意味
2. **効率性**: 手動 vs 自動の時間差
3. **信頼性**: エラー発生率
4. **利便性**: 実際に便利か

## 📊 効果測定指標

| 項目 | 手動運用 | 自動化後 | 改善率 |
|------|---------|----------|---------|
| タスク確認時間 | ? 分 | ? 秒 | ?% |
| タスク実行開始 | ? 分 | ? 秒 | ?% |
| エラー対処時間 | ? 分 | ? 分 | ?% |
| 報告作成時間 | ? 分 | ? 分 | ?% |

## 🎯 推奨アプローチ

### オプション1: CC02で完全テスト
CC02で Phase 1-4 を順番に実行し、問題点を洗い出す

### オプション2: CC02/CC03で分担テスト
- CC02: Phase 1-2（手動中心）
- CC03: Phase 3-4（自動化中心）

### オプション3: 一気に実装
両方同時に Phase 3 から開始

## 💡 即座に試せる最小テスト

```bash
# CC02用ワンライナー
export CLAUDE_AGENT_ID=CC02 && alias my-tasks="gh issue list --label cc02 --state open" && my-tasks

# 成功したら次のステップへ
```

どのアプローチで進めますか？