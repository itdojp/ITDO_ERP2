# 開発品質ゲート運用ガイド

## 📖 概要

ITDO ERP システムの開発では、段階的品質ゲート戦略を採用しています。これにより、開発を止めることなく品質を段階的に向上させ、実用的な CI/CD を実現します。

## 🎯 開発フェーズ

### Phase 1: 基盤安定期（現在）
**目標**: 基盤システムの安定性確保

#### ✅ 必須条件（MUST PASS）- マージブロック対象
- **基盤テスト**: 47テスト全て合格必須
  - `tests/unit/models/test_user_extended.py` (14 passed, 1 skipped)
  - `tests/unit/repositories/test_user_repository.py` (12 passed)
  - `tests/unit/test_models_user.py` (10 passed)
  - `tests/unit/test_security.py` (11 passed)
- **コード品質**: Ruff チェック・フォーマット合格
- **コンパイル**: 構文エラー 0件

#### ⚠️ 警告レベル（WARNING）- 通すが監視
- **サービス層テスト**: `tests/unit/services/` (現在5件失敗)
- **統合テスト**: 失敗しても警告表示のみ
- **カバレッジ**: 80%未満でも警告表示のみ

### Phase 2: 機能拡張期（予定）
**移行条件**:
- 基盤テスト 100% 合格継続（4週間）
- 主要機能のサービス層実装完了
- 警告テスト数 < 10個

### Phase 3: 本格運用期（予定）
**移行条件**:
- 全テスト 95% 合格
- セキュリティ監査完了
- 本番環境での負荷テスト完了

## 🔧 開発者向けコマンド

### マージ前チェック
```bash
# Phase 1 基準でマージ可能かチェック
make check-merge-ready

# 基盤テストのみ実行
make check-core-tests

# 開発フェーズ全体状況確認
make check-phase-status
```

### 結果の読み方
```bash
✅ = 合格（マージ可能）
❌ = 失敗（マージブロック）
⚠️ = 警告（マージ可能だが注意）
```

## 📋 日常運用

### 開発者チェックリスト
#### プッシュ前
- [ ] `make check-merge-ready` 実行
- [ ] 基盤テスト全て合格
- [ ] Ruff チェック合格

#### プルリクエスト作成前
- [ ] CI の "Core Foundation Tests" 合格確認
- [ ] サービス層テストの警告確認（Issue化）

#### レビュー担当者
- [ ] GitHub Actions の必須チェック合格確認
- [ ] 警告テストの Issue 存在確認

### 定期作業

#### 毎週金曜日（チームリーダー）
1. **警告テスト状況レビュー**
   ```bash
   make check-phase-status
   ```
2. **Issue 整理**
   - 新しい失敗テスト → Issue 作成
   - 解決済み Issue → クローズ
3. **Phase 移行判定**

#### 月次（プロジェクトマネージャー）
1. **Phase 移行判定会議**
2. **品質メトリクス確認**
3. **次フェーズ準備**

## 🚨 トラブルシューティング

### CI が失敗した場合

#### 基盤テスト失敗 → **開発停止**
```bash
# ローカル確認
make check-core-tests

# 個別テスト実行
cd backend
uv run pytest tests/unit/models/test_user_extended.py -v
```
**対応**: 即座に修正してプッシュ

#### サービス層テスト失敗 → **Issue化**
```bash
# 詳細確認
cd backend 
uv run pytest tests/unit/services/ -v --tb=short
```
**対応**: Issue 作成して継続開発

#### Ruff チェック失敗 → **開発停止**
```bash
# 自動修正
cd backend
uv run ruff check --fix .
uv run ruff format .
```

### よくある問題

#### Q: 基盤テストが急に失敗するようになった
A: 
1. `make clean` で一時ファイル削除
2. `make start-data` でデータ層起動確認
3. 依存関係の確認: `cd backend && uv sync`

#### Q: 警告テストを早急に修正したい
A:
1. Issue で優先度設定
2. Phase 2 移行時に自動的に必須になる
3. 緊急時は個別判断

## 📊 品質メトリクス

### 目標値
- **Phase 1**: 基盤テスト 100% + 全体 90%以上
- **Phase 2**: 全テスト 95%以上
- **Phase 3**: 全テスト 99%以上 + カバレッジ 85%以上

### 監視項目
- 基盤テスト合格率
- 警告テスト数の推移
- CI 実行時間
- 開発速度（Issue Close Rate）

## 📝 Issue管理ルール

### 失敗テスト Issue 作成
```markdown
# タイトル例
[TEST-FAILURE] test_user_service.py::test_export_user_list - AttributeError

# ラベル
- test-failure
- phase-1-warning (Phase 1では警告レベル)
- service-layer

# 優先度
- P1: 基盤テスト（即修正）
- P2: サービス層（Phase 2で必須）
- P3: 統合・E2E（Phase 3で必須）
```

### Issue ライフサイクル
1. **Open**: テスト失敗検出
2. **In Progress**: 修正作業中
3. **Review**: 修正完了、テスト中
4. **Closed**: テスト合格確認

## 🔄 CI/CD 設定

### GitHub Branch Protection
```yaml
# 必須チェック
required_status_checks:
  - "Core Foundation Tests (MUST PASS)"
  - "Code Quality (MUST PASS)"

# 警告のみ（必須ではない）
# - "Service Layer Tests (WARNING)"
# - "Test Coverage Report"
```

### ローカル pre-commit フック
```bash
# セットアップ
make pre-commit

# 自動実行内容
- make check-core-tests
- ruff check --fix
- ruff format
```

## 📈 継続改善

### フィードバックループ
1. **日次**: CI 結果確認
2. **週次**: 品質メトリクス確認  
3. **月次**: Phase 移行判定
4. **四半期**: 戦略見直し

### 改善提案
- 新しい品質チェック追加提案
- Phase 移行基準の調整提案  
- ツール改善提案

---

## 📞 サポート

### 困った時の連絡先
- **基盤テスト問題**: Tech Lead
- **CI/CD 問題**: DevOps チーム
- **Issue 管理**: Project Manager

### 参考リンク
- [GitHub Actions ログ](/.github/workflows/)
- [テスト結果詳細](/backend/htmlcov/)
- [Phase 管理 Issue](/.github/issues/)

---

*この文書は Phase 1 基準で作成されています。Phase 移行時に更新予定。*