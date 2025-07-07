# Issue着手時の共有手順

## Issue着手宣言の手順

### 1. Issue着手時の必須アクション
Issue処理を開始する際は、以下を**必ず**実行してください：

1. **Issueにコメント投稿**
   ```
   🚀 このissueの対応を開始します
   担当者: @[GitHubユーザー名]
   予定完了日: [yyyy-mm-dd]
   アプローチ: [簡潔な実装方針]
   ```

2. **ブランチ作成**
   ```bash
   git checkout -b feature/#[Issue番号]-[簡潔な説明]
   ```

3. **Draft PR作成**
   ```bash
   gh pr create --draft --title "[WIP] feat: [機能名] (Closes #[Issue番号])" --body "実装中..."
   ```

### 2. 進捗共有のタイミング

- **着手時**: Issue着手宣言
- **仕様確定時**: Draft PRに仕様書をコメント追加
- **実装完了時**: Draft状態を解除
- **レビュー要求時**: レビュアーをアサイン

### 3. 作業中断・引き継ぎ時

作業を中断する場合は、Issueに以下をコメント：
```
⏸️ 作業を一時中断します
理由: [中断理由]
現在の進捗: [完了項目]
次の担当者への引き継ぎ事項: [詳細]
```

### 4. 緊急時の連絡

- 重要な技術的課題や仕様変更が発生した場合
- Issueにコメント + Slackでメンション（チーム連絡先がある場合）

## GitHub Issue Labels活用

### 着手状況を示すラベル
- `status: in-progress` - 作業中
- `status: needs-review` - レビュー待ち
- `status: blocked` - ブロックされている

### 緊急度・重要度ラベル
- `priority: critical` - 緊急
- `priority: high` - 高優先度
- `priority: medium` - 中優先度
- `priority: low` - 低優先度

## 並行作業での注意事項

1. **依存関係の明確化**
   - 他のIssueに依存する場合は、Issue説明に明記
   - ブロック関係がある場合は事前に相談

2. **コンフリクト回避**
   - 同じファイルを編集する可能性がある場合は事前調整
   - 定期的な`git pull`とリベース

3. **テストデータの管理**
   - テスト用データベースの競合を避ける
   - 独立したテストケースを作成

## おすすめツール

### GitHub CLI活用
```bash
# Issue確認
gh issue view [issue_number]

# 着手宣言とブランチ作成
gh issue comment [issue_number] --body "🚀 作業開始します"
git checkout -b feature/#[issue_number]-[description]

# Draft PR作成
gh pr create --draft --title "[WIP] feat: ..." --body "..."
```

### Git hooks活用
```bash
# pre-commit hookでテスト自動実行
# pre-push hookで型チェック自動実行
```