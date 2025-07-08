# 現在の失敗テスト Issue 一覧

## 📋 Phase 1 警告レベル テスト失敗（5件）

以下のGitHub Issueを作成することを推奨します：

### Issue #1: [TEST-FAILURE] test_user_service.py::test_org_admin_cannot_create_cross_tenant
```markdown
**ラベル**: test-failure, P2-high, service-layer, phase-1-warning
**エラー**: pydantic_core._pydantic_core.ValidationError: role_ids Field required
**原因**: UserCreateExtended スキーマで role_ids が必須だが未提供
**Phase 1 影響**: 警告レベル ⚠️
```

### Issue #2: [TEST-FAILURE] test_user_service.py::test_cannot_delete_last_admin  
```markdown
**ラベル**: test-failure, P2-high, service-layer, phase-1-warning
**エラー**: Failed: DID NOT RAISE BusinessLogicError
**原因**: 最後のシステム管理者削除防止ロジック未実装
**Phase 1 影響**: 警告レベル ⚠️
```

### Issue #3: [TEST-FAILURE] test_user_service.py::test_get_user_permissions
```markdown
**ラベル**: test-failure, P2-high, service-layer, phase-1-warning  
**エラー**: AssertionError: assert 'read:*' in []
**原因**: ユーザー権限取得機能未実装
**Phase 1 影響**: 警告レベル ⚠️
```

### Issue #4: [TEST-FAILURE] test_user_service.py::test_user_activity_logging
```markdown
**ラベル**: test-failure, P2-high, service-layer, phase-1-warning
**エラー**: pydantic_core._pydantic_core.ValidationError: role_ids Field required  
**原因**: UserCreateExtended スキーマで role_ids が必須だが未提供
**Phase 1 影響**: 警告レベル ⚠️
```

### Issue #5: [TEST-FAILURE] test_user_service.py::test_export_user_list
```markdown
**ラベル**: test-failure, P2-high, service-layer, phase-1-warning
**エラー**: AttributeError: 'dict' object has no attribute 'content_type'
**原因**: エクスポート機能の戻り値形式が期待と異なる
**Phase 1 影響**: 警告レベル ⚠️
```

## 🎯 Issue 作成コマンド例

GitHub CLI を使用する場合：

```bash
# Issue #1
gh issue create \
  --title "[TEST-FAILURE] test_user_service.py::test_org_admin_cannot_create_cross_tenant - ValidationError: role_ids required" \
  --body "UserCreateExtended スキーマで role_ids が必須だが未提供されているため失敗。Phase 1では警告レベル。" \
  --label "test-failure,P2-high,service-layer,phase-1-warning"

# Issue #2  
gh issue create \
  --title "[TEST-FAILURE] test_user_service.py::test_cannot_delete_last_admin - 管理者削除防止ロジック未実装" \
  --body "最後のシステム管理者削除防止ロジックが未実装のため失敗。Phase 1では警告レベル。" \
  --label "test-failure,P2-high,service-layer,phase-1-warning"

# Issue #3
gh issue create \
  --title "[TEST-FAILURE] test_user_service.py::test_get_user_permissions - ユーザー権限取得機能未実装" \
  --body "ユーザー権限取得機能が未実装のため失敗。Phase 1では警告レベル。" \
  --label "test-failure,P2-high,service-layer,phase-1-warning"

# Issue #4
gh issue create \
  --title "[TEST-FAILURE] test_user_service.py::test_user_activity_logging - ValidationError: role_ids required" \
  --body "UserCreateExtended スキーマで role_ids が必須だが未提供されているため失敗。Phase 1では警告レベル。" \
  --label "test-failure,P2-high,service-layer,phase-1-warning"

# Issue #5  
gh issue create \
  --title "[TEST-FAILURE] test_user_service.py::test_export_user_list - エクスポート戻り値形式不一致" \
  --body "エクスポート機能の戻り値形式が期待と異なるため失敗。Phase 1では警告レベル。" \
  --label "test-failure,P2-high,service-layer,phase-1-warning"
```

## 📊 Issue 管理ダッシュボード

### Phase 1 品質状況
- ✅ **基盤テスト**: 47/47 合格（100%）
- ⚠️ **サービス層テスト**: 5件失敗（警告レベル）
- 📈 **全体成功率**: 91% (62/67 tests)

### Phase 2 移行準備
これらのIssueは Phase 2 移行時に必須修正対象となります：
- 現在の5件の失敗テスト
- 新規追加される機能テスト
- 統合テストの実装

### 定期レビュー
- **毎週金曜日**: Issue 状況確認
- **月次**: Phase 移行判定
- **Phase 2 移行時**: 全Issue P1昇格