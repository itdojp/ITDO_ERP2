# PR #96 緊急解決ガイド - CC02専用

## 🚨 2日以上停滞しているPR #96を本日中に解決する

### 📋 現状の問題分析
```yaml
問題:
  - CI未実行（GitHub Actionsが開始されない）
  - マージコンフリクトあり
  - 大規模PR（ファイル数多）
  - 最終更新から2日経過

原因推定:
  - GitHub Actions のキュー詰まり
  - 大規模変更によるタイムアウト
  - ベースブランチとの乖離
```

### 🛠️ Step-by-Step 解決手順

#### Step 1: 現状確認（5分）
```bash
# PRの詳細状態確認
gh pr view 96 --json state,mergeable,mergeStateStatus,statusCheckRollup

# ローカルにチェックアウト
git fetch origin
git checkout feature/organization-management

# 最新のmainとの差分確認
git fetch origin main
git diff origin/main --stat
```

#### Step 2: マージコンフリクト解決（30分）
```bash
# Option A: Rebase戦略（推奨）
git rebase origin/main

# コンフリクト解決
# 各ファイルを確認し、適切に統合
git status
# コンフリクトファイルを編集

# 解決後
git add .
git rebase --continue

# Option B: Merge戦略（rebaseが困難な場合）
git merge origin/main
# コンフリクト解決
git add .
git commit -m "Merge main and resolve conflicts"
```

#### Step 3: ローカルテスト実行（20分）
```bash
# Backend テスト
cd backend
uv run pytest -v
uv run mypy app/ --strict
uv run ruff check .

# Frontend テスト
cd ../frontend
npm test
npm run lint
npm run typecheck

# 全て成功することを確認
```

#### Step 4: CI強制実行（10分）
```bash
# Force push で PR更新
git push --force-with-lease origin feature/organization-management

# CI手動トリガー
gh workflow run ci.yml --ref feature/organization-management

# CI状態確認
gh run list --workflow=ci.yml --branch=feature/organization-management
```

#### Step 5: 代替案 - PR分割（CIが動かない場合）
```bash
# 新しいブランチで小規模PRを作成
git checkout main
git pull origin main

# 機能単位で分割
# Part 1: Backend基本機能
git checkout -b feature/org-management-backend-base
git cherry-pick <relevant-commits>
gh pr create --title "feat: Organization Management Backend (Part 1/4)"

# Part 2: Frontend基本機能
git checkout -b feature/org-management-frontend-base
git cherry-pick <relevant-commits>
gh pr create --title "feat: Organization Management Frontend (Part 2/4)"

# 以降、同様に分割
```

### 🎯 成功基準
```yaml
必須:
  ✅ CIが実行される
  ✅ 全テストがパス
  ✅ マージコンフリクト解決
  ✅ レビュー可能な状態

理想:
  ✅ 本日中にマージ
  ✅ または分割PR作成完了
```

### 💡 トラブルシューティング

#### CI が依然として実行されない場合
```bash
# 1. PR をドラフトに変更して再度Ready
gh pr ready 96 --undo
gh pr ready 96

# 2. 空コミットでトリガー
git commit --allow-empty -m "Trigger CI"
git push

# 3. PR再作成
gh pr close 96
git push origin feature/organization-management
gh pr create --title "feat: Organization Management System (Reopened)" --body "Previous PR #96"
```

#### テストが失敗する場合
```bash
# 最新の依存関係を確認
cd backend && uv sync
cd frontend && npm install

# 環境変数の確認
cp .env.example .env
# 必要な値を設定

# データベースマイグレーション
cd backend && uv run alembic upgrade head
```

### 📊 進捗報告テンプレート

19:00の報告用：
```markdown
## PR #96 対応進捗報告

### 完了事項
- [ ] 現状確認
- [ ] マージコンフリクト解決
- [ ] ローカルテスト成功
- [ ] CI実行試行

### 現在の状態
- CI状態: [実行中/未実行/成功/失敗]
- テスト結果: [成功/失敗 - 詳細]
- 残作業: [具体的な項目]

### 次のアクション
- [具体的な次の手順]

予定完了時刻: [時刻]
```

### 🚀 CC02への激励

```
CC02へ

PR #96は確かに困難な課題ですが、
あなたの技術力なら必ず解決できます。

一つずつ、着実に進めていけば
必ずゴールに到達します。

困ったときは遠慮なく
CC03やチームに相談してください。

今日中の解決を信じています！
```

---

**緊急度**: 最高
**期限**: 本日20:00まで
**サポート**: CC03が技術支援可能