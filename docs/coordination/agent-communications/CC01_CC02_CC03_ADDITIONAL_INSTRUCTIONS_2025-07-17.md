# 🤖 CC01, CC02, CC03 エージェント追加指示書

**発行日時**: 2025年7月17日 18:00 JST  
**発行者**: Claude Code (CC01) - システム統合担当  
**対象**: CC01 (フロントエンド), CC02 (バックエンド), CC03 (インフラ/テスト)

## 📊 現在の状況分析

### システム導入完了状況
- **ラベルベース処理システム**: ✅ 完全稼働
- **GitHub Actions**: ✅ 15ワークフロー正常動作
- **リポジトリ整理**: ✅ 98.2%クリーンアップ完了
- **エージェント協調体制**: 🟡 90% (CC03制限付き)

### 現在のIssue状況
- **オープンIssue**: 10件確認済み
- **処理ラベル付与**: 未実施（手動設定が必要）
- **優先度**: Issue #173 (自動割り当てシステム改善) が最優先

## 🎯 各エージェント別追加指示

### CC01 - フロントエンド専門エージェント

#### 🔥 緊急アクション
1. **Issue #172 処理**: UI Component Design Issue #160 Implementation Report
   - 現在ラベル未設定のため `claude-code-frontend` ラベル追加推奨
   - UI/UXデザインシステムの完成度確認

2. **Issue #25**: Type-safe Dashboard and Analytics Implementation
   - React 18 + TypeScript 5での実装
   - `claude-code-frontend` + `tdd-required` ラベル設定

3. **Issue #23**: Type-safe Project Management Implementation
   - プロジェクト管理画面の実装
   - Tailwind CSSとアクセシビリティ準拠

#### 📋 専門分野タスク
- **技術スタック**: React 18, TypeScript 5, Vite, Tailwind CSS
- **品質基準**: 厳密な型定義, レスポンシブデザイン, >80% テストカバレッジ
- **処理ラベル**: `claude-code-frontend`, `claude-code-urgent`, `claude-code-ready` (UI/UX関連)

### CC02 - バックエンド専門エージェント

#### 🔥 緊急アクション
1. **Issue #46**: セキュリティ監査ログとモニタリング機能
   - `claude-code-backend` + `claude-code-security` ラベル設定
   - Keycloak OAuth2/OIDC統合

2. **Issue #42**: 組織・部門管理API実装と階層構造サポート
   - SQLAlchemy 2.0 Mapped型使用
   - PostgreSQL 15最適化

3. **Issue #40**: ユーザー権限・ロール管理API実装
   - `claude-code-backend` + `claude-code-database` ラベル設定
   - 非同期処理とTDD準拠

#### 📋 専門分野タスク
- **技術スタック**: Python 3.13, FastAPI, SQLAlchemy 2.0, PostgreSQL 15
- **品質基準**: async/await必須, 型安全性, セキュリティ準拠
- **処理ラベル**: `claude-code-backend`, `claude-code-database`, `claude-code-security`

### CC03 - インフラ/テスト専門エージェント

#### ⚠️ 現在の制限事項
- **Bashエラー**: `/root/.claude/shell-snapshots/` 問題継続中
- **対処法**: Read/Write/Edit/Grep ツール使用継続
- **推奨**: Claude Codeセッション再起動による完全復旧

#### 🔥 緊急アクション (代替手段使用)
1. **Issue #173**: 自動割り当てシステム改善
   - 現在cc03ラベル付き、`claude-code-infrastructure` 追加推奨
   - GitHub Actions ワークフローの最適化

2. **Issue #44**: 統合テストカバレッジ拡張とE2Eテスト実装
   - `claude-code-testing` + `tdd-required` ラベル設定
   - pytest + vitest の統合テスト

3. **Issue #45**: APIドキュメントとOpenAPI仕様の充実
   - `claude-code-infrastructure` + `api-design` ラベル設定

#### 📋 専門分野タスク
- **技術スタック**: GitHub Actions, pytest, vitest, Docker/Podman
- **品質基準**: CI/CD最適化, >80%カバレッジ, パフォーマンス
- **処理ラベル**: `claude-code-infrastructure`, `claude-code-testing`

## 🚀 実践的アクションプラン

### 即座実行事項 (1時間以内)

#### 1. ラベル設定の実行
各エージェントは担当Issueに適切なラベルを追加:
```bash
# CC01: フロントエンド関連
gh issue edit 172 --add-label "claude-code-frontend"
gh issue edit 25 --add-label "claude-code-frontend,tdd-required"
gh issue edit 23 --add-label "claude-code-frontend,ui-ux"

# CC02: バックエンド関連
gh issue edit 46 --add-label "claude-code-backend,claude-code-security"
gh issue edit 42 --add-label "claude-code-backend,claude-code-database"
gh issue edit 40 --add-label "claude-code-backend,organization-mgmt"

# CC03: インフラ/テスト関連 (代替手段使用)
gh issue edit 173 --add-label "claude-code-infrastructure"
gh issue edit 44 --add-label "claude-code-testing,tdd-required"
gh issue edit 45 --add-label "claude-code-infrastructure,api-design"
```

#### 2. GitHub Actions動作確認
- ラベル追加後、`label-processor.yml` の自動処理確認
- 処理開始時に `claude-code-processing` ラベル付与確認
- エラー発生時は `claude-code-failed` ラベル使用

#### 3. 協調体制の確立
- `docs/coordination/` ディレクトリでの進捗報告
- 相互依存タスクの調整
- 問題発生時の迅速な情報共有

### 品質基準遵守

#### 必須要件
- **TDD準拠**: テストファースト開発
- **型安全性**: TypeScript strict mode, mypy --strict
- **テストカバレッジ**: >80%
- **API応答時間**: <200ms
- **セキュリティ**: 認証・認可の適切な実装

#### 技術標準
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.0
- **Frontend**: React 18 + TypeScript 5 + Vite
- **Database**: PostgreSQL 15 + Redis 7
- **Testing**: pytest + vitest
- **CI/CD**: GitHub Actions

## 📊 成功指標とKPI

### 週間目標
- **処理Issue数**: 30-60件 (全エージェント合計)
- **成功率**: >95%
- **平均処理時間**: <15分/Issue
- **品質スコア**: >90%

### 個別目標
- **CC01**: フロントエンド関連 8-12件/週
- **CC02**: バックエンド関連 10-15件/週
- **CC03**: インフラ/テスト関連 8-12件/週

## 🔍 エスカレーション基準

### claude-code-failed ラベル使用条件
1. **技術的制約**: 15分以上解決できない問題
2. **アーキテクチャ変更**: 既存設計の大幅変更が必要
3. **外部依存**: 新しいライブラリ・サービスが必要
4. **セキュリティリスク**: 潜在的なセキュリティ問題

### 協調が必要な場合
- **フロントエンド⇔バックエンド**: API設計の調整
- **バックエンド⇔インフラ**: データベース最適化、セキュリティ設定
- **インフラ⇔フロントエンド**: CI/CD最適化、パフォーマンス測定

## 💬 コミュニケーション例

### 処理開始時
```markdown
🎯 ITDO_ERP2 [専門分野] 処理開始

**Issue**: #XXX
**Component**: [詳細]
**Technology**: [技術スタック]
**Estimated Time**: X分

Processing Steps:
- [ ] 要件分析
- [ ] 実装
- [ ] テスト作成
- [ ] 品質チェック
```

### 処理完了時
```markdown
✅ ITDO_ERP2 [専門分野] 処理完了

**Implemented**:
- [具体的な実装内容]

**Quality Checks**:
- ✓ 型安全性確認
- ✓ テスト通過 (カバレッジ X%)
- ✓ 品質基準準拠

**Next Step**: レビューとマージ待ち
```

## 🎯 最終確認事項

### 各エージェントチェックリスト
- [ ] 担当Issue特定と優先度確認
- [ ] 適切なラベル設定
- [ ] 技術スタックと品質基準の理解
- [ ] エスカレーション基準の把握
- [ ] 協調体制の確認

### システム確認
- [ ] GitHub Actions正常動作
- [ ] ラベルベース処理システム稼働
- [ ] 品質ゲート通過
- [ ] 協調ディレクトリ活用

---

**重要**: CC03のBashエラーは継続中ですが、代替手段で作業継続可能です。完全復旧にはClaude Codeセッション再起動を推奨します。

**成功の鍵**: 各エージェントの専門性を活かし、ラベルベース処理システムで効率的な協調開発を実現することです。

**Next Action**: 各エージェントは即座にラベル設定を実行し、Issue処理を開始してください。