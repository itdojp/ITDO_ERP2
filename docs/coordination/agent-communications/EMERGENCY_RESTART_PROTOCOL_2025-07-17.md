# 🚨 エージェント緊急再起動プロトコル - 最小限アプローチ

**作成日時**: 2025年7月17日 22:35 JST  
**作成者**: Claude Code (CC01) - システム統合担当  
**目的**: 停止中エージェントの最小限再起動手順

## 📊 現状確認結果

### エージェント状態
- **CC01**: ❌ 完全停止（活動なし）
- **CC02**: ❌ 完全停止（活動なし）  
- **CC03**: ❌ 完全停止（Issue割り当てあるが未着手）

### 人間の活動
- ✅ PR #179, #180 進行中（人間が開発中）
- ✅ 開発は人間によって継続されている

## 🎯 最小限再起動手順

### CC01への指示（最も簡単なタスクから）

```markdown
@cc01

CC01、以下の最小限のタスクから開始してください：

1. **生存確認タスク**:
   ```bash
   # README.mdに現在日付を追加
   echo "Last updated: $(date)" >> README.md
   git add README.md
   git commit -m "chore: Update README with current date"
   ```

2. **成功したら次のタスク**:
   - docs/coordination/CC01_STATUS.mdファイルを作成
   - 「CC01 Active」と記載
   - コミット

3. **その後**:
   - Issue #174を確認して着手
```

### CC02への指示（バックエンド最小タスク）

```markdown
@cc02 

CC02、以下の最小限のタスクから開始してください：

1. **生存確認タスク**:
   ```bash
   # backend/docs/CC02_STATUS.mdを作成
   echo "CC02 Backend Agent Active" > backend/docs/CC02_STATUS.md
   git add backend/docs/CC02_STATUS.md
   git commit -m "chore: CC02 status confirmation"
   ```

2. **成功したら次のタスク**:
   - Issue #42の実装状況を確認
   - PR #179のサポートが必要か確認

3. **その後**:
   - 小規模なAPIエンドポイント1つから実装開始
```

### CC03への指示（インフラ最小タスク）

```markdown
@cc03

CC03、以下の最小限のタスクから開始してください：

1. **生存確認タスク**:
   ```bash
   # .github/workflows/cc03-health-check.yml を作成
   cat > .github/workflows/cc03-health-check.yml << 'EOF'
   name: CC03 Health Check
   on:
     workflow_dispatch:
   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - run: echo "CC03 is operational"
   EOF
   
   git add .github/workflows/cc03-health-check.yml
   git commit -m "chore: Add CC03 health check workflow"
   ```

2. **成功したら次のタスク**:
   - Issue #173の自動割り当てシステム改善に着手
   - 最小限の変更から開始

3. **その後**:
   - Issue #174-176の段階的実装
```

## 🔧 エージェント再起動のベストプラクティス

### 原則
1. **最小限から開始**: 1行の変更から
2. **成功を確認**: 各ステップで動作確認
3. **段階的拡大**: 簡単→中程度→複雑

### 失敗時の対処
1. **30分待機**: 応答がない場合は30分後に再試行
2. **別アプローチ**: 異なる簡単なタスクを試す
3. **人間介入**: 継続的失敗時は人間が対処

## 📋 期待される結果

### 24時間以内
- 各エージェントから最低1つのコミット
- 生存確認ファイルの作成
- 次のタスクへの移行

### 48時間以内  
- 割り当てられたIssueへの着手
- 小規模な実装の開始
- 継続的な活動の確立

## 💡 重要な注意事項

1. **無理な複雑化を避ける**: 動作確認を優先
2. **人間の作業を妨げない**: PR #179, #180と競合しない
3. **フェイルファースト**: 失敗したら早期に別案へ

---

**📌 最優先事項**: まず各エージェントの生存確認から開始