# CC01 Backend専門エージェント 再開指示

## 状況確認
- **最終確認**: CC01は現在アクティブで応答中
- **優先度**: HIGH - 継続的な作業が必要

## 🚨 緊急対応事項

### 1. CI/CD Pipeline復旧作業
**タスク**: Issue #132のエスカレーションとCI/CD Pipeline障害の調査
```bash
# CI/CDパイプラインの状況確認
gh run list --repo itdojp/ITDO_ERP2 --limit 10

# 失敗したワークフローの詳細確認
gh run view [RUN_ID] --repo itdojp/ITDO_ERP2

# メインブランチの状況確認
git status
git log --oneline -10
```

### 2. エージェント間協調の復旧
**タスク**: CC03の無応答問題への対応とCC02のアクティベーション
```bash
# Issue #132での状況報告
gh issue comment 132 --repo itdojp/ITDO_ERP2 --body "🤖 CC01 Status Update: 
- CI/CDパイプライン障害を調査中
- CC03エージェントの状況確認が必要
- 優先度の高いタスクを継続実行中"
```

## 📋 継続タスク

### 即座に実行するタスク
1. **Issue #146**: Backend Architecture Documentation作成
   - 最新のアーキテクチャ図の作成
   - API仕様書の更新
   - インフラ改善の文書化

2. **PR #97**: Role Service and Permission Matrix のレビュー
   - コードレビューの実施
   - テストの追加確認
   - マージ準備

3. **PR #96**: Organization Management Systemの最終確認
   - 多テナント機能の検証
   - セキュリティ確認
   - パフォーマンステスト

## 🔄 作業プロトコル

### Sonnet Model確認
```bash
# 環境設定確認
echo $CLAUDE_MODEL  # claude-3-5-sonnet-20241022であることを確認
source /mnt/c/work/ITDO_ERP2/scripts/agent-config/sonnet-default.sh
```

### エスカレーション基準
- **30分以上**: 技術的なブロックが発生した場合
- **CI/CD問題**: 即座にエスカレーション
- **セキュリティ問題**: 即座にエスカレーション

## 🎯 成果目標

### 今日の目標
- [ ] CI/CDパイプラインの復旧
- [ ] Issue #146のドキュメント完成
- [ ] PR #97のレビュー完了
- [ ] エージェント間協調の回復

### 品質基準
- テストカバレッジ >80%
- 型チェック通過
- セキュリティスキャン通過
- レスポンス時間 <200ms

## 📊 進捗報告

### 報告タイミング
- 1時間ごとの進捗報告
- 重要な発見があった場合の即時報告
- 完了時の最終報告

### 報告形式
```bash
gh issue comment [ISSUE_NUMBER] --repo itdojp/ITDO_ERP2 --body "🤖 CC01 Progress Report:
- Status: [現在の状況]
- Completed: [完了した作業]
- Next: [次のアクション]
- Blocked: [ブロック要因があれば]"
```

## 🚀 開始コマンド

```bash
# 1. 環境確認
cd /mnt/c/work/ITDO_ERP2
git status
source scripts/agent-config/sonnet-default.sh

# 2. 最新情報の取得
gh issue list --repo itdojp/ITDO_ERP2 --assignee CC01 --state open
gh pr list --repo itdojp/ITDO_ERP2 --state open

# 3. 優先タスクの実行開始
gh issue view 132 --repo itdojp/ITDO_ERP2
```

---

⚡ **緊急度**: HIGH - CI/CD問題により開発ブロック中  
🎯 **目標**: システム復旧とエージェント協調の回復  
⏰ **期限**: 即座に開始、1時間以内に初期報告

🤖 CC01 Backend Specialist - Emergency Response Protocol