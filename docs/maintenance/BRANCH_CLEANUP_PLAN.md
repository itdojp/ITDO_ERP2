# ブランチ整理計画

**作成日:** 2025年7月11日  
**目的:** 未マージブランチの整理と管理方針の確立

## 📋 現状分析

### ブランチ統計
- **総リモートブランチ数:** 20
- **未マージブランチ数:** 19
- **アクティブPR数:** 5

## 🎯 整理方針

### 1. 即時保持（アクティブPR）
| ブランチ名 | PR# | 状態 | 理由 |
|-----------|-----|------|------|
| feature/task-department-integration-CRITICAL | #98 | 95%完了 | Phase 3必須 |
| feature/role-service | #97 | 70%完了 | Phase 3必須 |
| feature/organization-management | #96 | 検討中 | Phase 2関連 |
| feature/e2e-test-implementation | #95 | 90%完了 | Phase 3必須 |
| feature/issue-92-task-management-complete | #94 | 検討中 | Task管理実装 |

### 2. 削除推奨（完了済み機能）
| ブランチ名 | 最終コミット | 削除理由 |
|-----------|-------------|----------|
| feature/user-management | 3bcb8e0 | Phase 1完了・mainにマージ済み |
| feature/keycloak-integration | ed13714 | 認証実装完了・mainに統合済み |
| feature/type-safe-user-api | 432c0b3 | UserService完了・#80でマージ済み |
| fix/test-database-cleanup | 2c2ac5c | 修正適用済み |
| feature/phase2-organization-service | 860cfe6 | 組織管理実装済み |
| feature/department-service-phase2 | 27aabc4 | 部署管理実装済み |
| feature/issue-64-cleanup-and-ruff-fixes | 89930b1 | #67でマージ済み |
| chore/issue-57-branch-cleanup | ac3de62 | クリーンアップスクリプト作成済み |

### 3. 削除推奨（置換済み）
| ブランチ名 | 置換先 | 削除理由 |
|-----------|--------|----------|
| feature/task-management | PR #94 | 新実装で置換 |
| feature/issue-75-task-management-v2 | PR #94 | 統合済み |
| feature/type-safe-task-management | PR #94 | 型安全実装完了 |
| feature/dashboard-progress | Phase 4 | UIで再実装予定 |

### 4. 保持検討（将来使用）
| ブランチ名 | 保持理由 | 使用予定 |
|-----------|---------|----------|
| feature/dashboard | UI基礎実装あり | Phase 4で活用可能 |
| feature/project-management | プロジェクト管理設計 | Phase 5で検討 |

## 🔧 実行手順

### ステップ1: バックアップ作成
```bash
# ブランチ情報の保存
git branch -r --no-merged origin/main > docs/maintenance/unmerged-branches-$(date +%Y%m%d).txt
```

### ステップ2: 段階的削除

#### Phase A: 確実に不要なブランチ（8個）
```bash
# マージ済み機能ブランチの削除
git push origin --delete feature/user-management
git push origin --delete feature/keycloak-integration
git push origin --delete feature/type-safe-user-api
git push origin --delete fix/test-database-cleanup
git push origin --delete feature/phase2-organization-service
git push origin --delete feature/department-service-phase2
git push origin --delete feature/issue-64-cleanup-and-ruff-fixes
git push origin --delete chore/issue-57-branch-cleanup
```

#### Phase B: 置換済みブランチ（4個）
```bash
# 新実装で置換されたブランチの削除
git push origin --delete feature/task-management
git push origin --delete feature/issue-75-task-management-v2
git push origin --delete feature/type-safe-task-management
git push origin --delete feature/dashboard-progress
```

#### Phase C: PR完了後の削除（5個）
```bash
# 各PRマージ後に実行
# PR #98 マージ後
git push origin --delete feature/task-department-integration-CRITICAL

# PR #97 マージ後
git push origin --delete feature/role-service

# 以下同様...
```

## 📊 期待される結果

### 整理前
- リモートブランチ: 20個
- 未マージ: 19個

### Phase A+B実行後
- リモートブランチ: 8個（12個削除）
- 未マージ: 7個

### 全PR完了後
- リモートブランチ: 3個（main + 将来使用2個）
- 未マージ: 2個

## ⚠️ 注意事項

1. **削除前の確認**
   - 本当に不要か最終確認
   - 他のメンバーが使用していないか確認
   - バックアップが取れているか確認

2. **段階的実行**
   - 一度に全て削除せず、段階的に実行
   - 各段階後に動作確認

3. **ドキュメント化**
   - 削除したブランチと理由を記録
   - 将来の参考のため保存

## 🔍 削除コマンドの安全な実行

```bash
# 削除前の最終確認（ドライラン）
for branch in feature/user-management feature/keycloak-integration; do
  echo "Would delete: $branch"
  git log origin/main..$branch --oneline | head -1
done

# 実際の削除（1つずつ確認しながら）
read -p "Delete feature/user-management? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  git push origin --delete feature/user-management
fi
```

## 📅 実施スケジュール

1. **即日実施可能:** Phase A（マージ済み8ブランチ）
2. **1週間以内:** Phase B（置換済み4ブランチ）
3. **PR完了時:** Phase C（各PR完了後に削除）

---

*この計画は2025年7月11日に作成されました。実行前に最新状況を確認してください。*