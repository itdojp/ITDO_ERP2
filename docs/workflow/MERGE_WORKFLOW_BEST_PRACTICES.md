# マージワークフロー ベストプラクティス

**作成日:** 2025年7月11日  
**目的:** 未マージブランチの蓄積を防ぐ適切なワークフロー確立

## 🔍 現在の問題の原因

### **問題の根本原因**
```bash
# 現在の開発パターン
1. ブランチでPR作成 → feature/xxx
2. PRレビュー・修正
3. PR未マージのまま → 直接mainにコミット ❌
4. ブランチが残り続ける → 蓄積
```

### **発生している事象**
- 19個の未マージブランチ
- PRは存在するが、正式マージされていない
- 機能は実装済みだが、ブランチ管理が不適切

## ✅ 推奨ワークフロー

### **標準的なPRマージフロー**
```bash
# 1. ブランチ作成・開発
git checkout -b feature/new-feature
# 開発作業
git add . && git commit -m "feat: implement new feature"
git push origin feature/new-feature

# 2. PR作成
gh pr create --title "feat: implement new feature" --body "..."

# 3. レビュー・修正
# PR修正作業

# 4. 正式マージ
gh pr merge 123 --squash --delete-branch  # ✅ 重要: --delete-branch

# 5. ローカル清掃
git checkout main
git pull origin main
git branch -d feature/new-feature  # ローカルブランチ削除
```

### **GitHubの自動削除設定**
Repository Settings → General → Pull Requests
- ✅ **"Automatically delete head branches"** を有効化

## 🎯 今後の具体的な手順

### **Phase 3 PRs完了時**
```bash
# PR #98 (Task-Department Integration)
1. PR最終修正完了
2. CI/CD全通過確認
3. gh pr merge 98 --squash --delete-branch
4. feature/task-department-integration-CRITICAL 自動削除 ✅

# PR #97 (Role Service)
1. Core Foundation Tests修正
2. Backend Tests通過
3. gh pr merge 97 --squash --delete-branch
4. feature/role-service 自動削除 ✅

# 以下同様...
```

### **新規開発時（Phase 4以降）**
```bash
# UI実装例
1. git checkout -b feature/login-ui
2. 開発・テスト・コミット
3. gh pr create --title "feat: implement login UI"
4. レビュー・修正
5. gh pr merge XXX --squash --delete-branch
6. ブランチ自動削除 ✅
```

## 🔧 設定変更の推奨

### **1. GitHub Repository設定**
```bash
# Settings → General → Pull Requests
✅ Automatically delete head branches
✅ Allow squash merging
✅ Allow merge commits
❌ Allow rebase merging (混乱を避けるため)
```

### **2. Branch Protection Rules**
```bash
# Settings → Branches → Add rule
Branch name pattern: main
✅ Require pull request reviews before merging
✅ Require status checks to pass before merging
✅ Require branches to be up to date before merging
```

### **3. Claude Code エージェント用コマンド**
```bash
# PRマージ時の標準コマンド
gh pr merge [PR番号] --squash --delete-branch

# 複数PR一括処理
for pr in 98 97 95; do
  echo "Merging PR #$pr"
  gh pr merge $pr --squash --delete-branch
done
```

## 📊 効果予測

### **現在の状況**
- リモートブランチ: 20個
- 未マージブランチ: 19個
- 管理負荷: 高

### **適切なワークフロー適用後**
- リモートブランチ: 1個（main）
- 未マージブランチ: 0個
- 管理負荷: 低

## 🚨 注意事項

### **マージ時のチェック項目**
1. ✅ **CI/CD全通過**: 全テストが成功
2. ✅ **コンフリクト解消**: マージ可能状態
3. ✅ **レビュー完了**: 必要なApproval取得
4. ✅ **ブランチ削除**: --delete-branchオプション使用

### **避けるべき操作**
```bash
# ❌ PR未マージで直接mainにコミット
git checkout main
git add . && git commit -m "feat: bypass PR"

# ✅ 正しい方法
# PR経由で必ずマージ
```

## 🔄 移行期の対応

### **既存PRの処理**
1. **現在のPR (#98, #97, #95, #94, #96)**
   - 修正完了後、正式マージ
   - --delete-branchオプション使用

2. **古いブランチ**
   - 段階的削除（前回の計画通り）
   - 削除前にバックアップ

### **新規開発から適用**
- Phase 4 UI実装から新ワークフロー適用
- 全てのPRで--delete-branchオプション使用

## 💡 Claude Code エージェント向けガイド

### **PR作成時**
```bash
# 1. ブランチ作成
git checkout -b feature/issue-XXX-description

# 2. 開発・テスト
# 開発作業

# 3. PR作成
gh pr create --title "feat: implement feature XXX" --body "..."

# 4. Draft → Ready for Review
gh pr ready [PR番号]
```

### **PR完了時**
```bash
# 1. 最終テスト実行
make test-full

# 2. CI/CD確認
gh pr checks [PR番号]

# 3. マージ実行
gh pr merge [PR番号] --squash --delete-branch

# 4. 確認
git checkout main && git pull origin main
```

## 📋 結論

**今後は問題発生しません**：
- ✅ 適切なPRマージフロー
- ✅ 自動ブランチ削除
- ✅ 一貫したワークフロー

**移行期間中のアクション**：
1. GitHub設定変更（自動削除有効化）
2. 既存PRの正式マージ
3. 古いブランチの段階的削除
4. 新規開発から新ワークフロー適用

---

*このワークフローを確立することで、ブランチ管理の問題は根本的に解決されます。*