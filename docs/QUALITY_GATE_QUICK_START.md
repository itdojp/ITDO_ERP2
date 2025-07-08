# 🚀 品質ゲート クイックスタート

## 📖 新規開発者向け 5分ガイド

### 1. マージ前の必須チェック
```bash
# Phase 1 基準でマージ可能かチェック
make check-merge-ready

# 結果の見方:
# ✅ = 合格（マージ可能）
# ❌ = 失敗（マージブロック）  
# ⚠️ = 警告（マージ可能だが注意）
```

### 2. 現在のルール（Phase 1: 基盤安定期）

#### 🚨 **マージブロック（即修正必須）**
- 基盤テスト失敗（47テスト）
- Ruff チェック失敗
- コンパイルエラー

#### ⚠️ **警告レベル（マージ可能）**
- サービス層テスト失敗（5件既知）
- 統合テスト失敗
- カバレッジ不足

### 3. 日常の開発フロー

#### プッシュ前
```bash
make check-core-tests    # 基盤テストのみ実行
```

#### プルリクエスト前
```bash
make check-merge-ready   # 完全チェック
```

#### 失敗時の対応
```bash
# 基盤テスト失敗 → 即修正
cd backend
uv run pytest tests/unit/models/test_user_extended.py -v

# Ruff 失敗 → 自動修正
cd backend  
uv run ruff check --fix .
uv run ruff format .
```

## 🎯 Phase移行予定

### Phase 1 → Phase 2 条件
- 基盤テスト 100% 継続（4週間）
- サービス層実装完了
- 警告テスト < 10件

### Phase 2以降
警告レベルテストが段階的に必須レベルに昇格

## 📞 困った時

### エラー対応
- **基盤テスト**: [品質ゲートガイド](./development-quality-gates.md)
- **CI失敗**: GitHub Actions ログ確認
- **不明点**: Tech Lead に相談

### 関連ドキュメント
- [詳細運用ガイド](./development-quality-gates.md)
- [Issue管理](./current-test-failures-issues.md)
- [CI設定](../.github/workflows/ci-development.yml)

---

**🎉 開発を止めずに品質向上！Phase 1 で安心開発を始めましょう！**