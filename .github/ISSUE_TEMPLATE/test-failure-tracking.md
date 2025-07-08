---
name: テスト失敗追跡
about: 失敗しているテストの追跡と管理
title: '[TEST-FAILURE] テストファイル名::テスト関数名 - エラー概要'
labels: 'test-failure, needs-investigation'
assignees: ''
---

# テスト失敗追跡

## 📍 基本情報

**失敗テスト**: `tests/unit/services/test_user_service.py::TestUserService::test_example`

**失敗カテゴリ**: 
- [ ] 基盤テスト（P1: 即修正必須）
- [x] サービス層テスト（P2: Phase 2で必須）
- [ ] 統合テスト（P3: Phase 3で必須）

**現在のPhase影響**:
- [ ] Phase 1: マージブロック対象 🚨
- [x] Phase 1: 警告レベル ⚠️

## 🐛 エラー詳細

### エラーメッセージ
```
TypeError: 'password' is an invalid keyword argument for User
```

### 再現手順
```bash
cd backend
uv run pytest tests/unit/services/test_user_service.py::TestUserService::test_example -v
```

### 期待する動作
ユーザー作成が正常に動作すること

### 実際の動作
TypeErrorが発生してテストが失敗

## 📊 影響範囲

**依存関係**:
- [ ] 他のテストに影響あり
- [x] 単独テストのみ

**機能影響**:
- [ ] 基盤機能に影響
- [x] 特定機能のみ
- [ ] 影響範囲不明

## 🔧 対応方針

### Phase 1（現在）
- [x] 警告として監視
- [ ] Issue化済み
- [ ] 修正予定なし（Phase 2で対応）

### Phase 2移行時の対応
- [ ] 必須修正対象に昇格
- [ ] 修正担当者アサイン
- [ ] 修正期限設定

## 📝 調査メモ

### 原因調査
```markdown
User モデルが 'password' パラメータを直接受け取らない。
'hashed_password' または User.create() メソッドを使用する必要がある。
```

### 修正方針案
```markdown
UserRepository.create() メソッドを修正して、
User.create() クラスメソッドを使用するように変更する。
```

## 🔗 関連Issue・PR

- 関連Issue: #XXX
- 修正PR: #XXX
- 依存Issue: #XXX

## ✅ 完了条件

- [ ] テストが合格すること
- [ ] 関連テストが破綻しないこと
- [ ] 機能仕様に影響がないこと
- [ ] ドキュメント更新（必要に応じて）

## 📅 タイムライン

- **発見**: 2025-01-XX
- **Phase 2 必須化**: 2025-XX-XX（予定）
- **修正期限**: Phase 2 移行時
- **完了**: 未定

---

## 🏷️ ラベル使用ガイド

### 優先度
- `P1-critical`: 基盤テスト（即修正）
- `P2-high`: サービス層（Phase 2必須）
- `P3-medium`: 統合テスト（Phase 3必須）

### カテゴリ
- `test-failure`: テスト失敗
- `phase-1-warning`: Phase 1警告レベル
- `service-layer`: サービス層関連
- `model-layer`: モデル層関連
- `repository-layer`: リポジトリ層関連