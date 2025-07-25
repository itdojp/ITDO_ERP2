# 🤖 ITDO_ERP2 エージェント指示書

## 📋 概要

ITDO_ERP2プロジェクト専用のエージェント指示書です。ラベルベース処理システムを使用して効率的な開発を実現します。

## 🏷️ ラベルベース処理システム

### 処理指示ラベル（これらが付いているIssueのみ処理）

| ラベル | 対象 | 技術スタック |
|--------|------|-------------|
| `claude-code-ready` | 汎用処理 | 全般 |
| `claude-code-urgent` | 緊急処理 | 全般（高優先度） |
| `claude-code-backend` | バックエンド | FastAPI, Python 3.13, SQLAlchemy 2.0 |
| `claude-code-frontend` | フロントエンド | React 18, TypeScript 5, Vite |
| `claude-code-testing` | テスト | pytest, vitest, >80% coverage |
| `claude-code-infrastructure` | インフラ | GitHub Actions, Podman, CI/CD |
| `claude-code-database` | データベース | PostgreSQL 15, Alembic, Redis 7 |
| `claude-code-security` | セキュリティ | Keycloak, OAuth2/OIDC |

### 除外ラベル（これらが付いているIssueは処理しない）

```
discussion, design, on-hold, manual-only, blocked, wontfix, duplicate, invalid
```

## 👥 エージェント専門化

### CC01 - フロントエンド専門
- **主担当**: `claude-code-frontend`
- **副担当**: `claude-code-urgent`, `claude-code-ready` (UI/UX関連)
- **技術領域**: React 18, TypeScript 5, Vite, Tailwind CSS
- **品質基準**: 厳密な型定義, レスポンシブデザイン, アクセシビリティ

### CC02 - バックエンド専門
- **主担当**: `claude-code-backend`, `claude-code-database`
- **副担当**: `claude-code-security`
- **技術領域**: Python 3.13, FastAPI, SQLAlchemy 2.0, PostgreSQL 15
- **品質基準**: async/await必須, 型安全性, セキュリティ準拠

### CC03 - インフラ/テスト専門
- **主担当**: `claude-code-infrastructure`, `claude-code-testing`
- **副担当**: `claude-code-ready` (CI/CD関連)
- **技術領域**: GitHub Actions, pytest, vitest, Docker/Podman
- **品質基準**: CI/CD最適化, >80%カバレッジ, パフォーマンス

## 📋 処理手順

### 1. Issue確認
```
✅ 処理指示ラベルがある
✅ 除外ラベルがない
✅ 自分の専門分野
✅ 他エージェントが処理中でない（claude-code-processing未付与）
```

### 2. 処理開始
```
1. claude-code-processing ラベル追加
2. 処理開始コメント投稿
3. 実装・テスト・ドキュメント作成
4. 品質チェック実行
```

### 3. 処理完了
```
1. claude-code-completed または claude-code-failed ラベル追加
2. claude-code-processing ラベル削除
3. 詳細な完了報告コメント投稿
```

## 🎯 ITDO_ERP2 品質基準

### 必須要件
- **TDD準拠**: テストファースト開発
- **型安全性**: TypeScript strict mode, mypy --strict
- **テストカバレッジ**: >80%
- **パフォーマンス**: API応答時間 <200ms
- **セキュリティ**: 認証・認可の適切な実装

### 技術標準
- **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.0
- **Frontend**: React 18 + TypeScript 5 + Vite
- **Database**: PostgreSQL 15 + Redis 7
- **Testing**: pytest + vitest
- **CI/CD**: GitHub Actions

## 🚫 禁止事項

1. **ラベルなしIssueの処理** - 絶対禁止
2. **除外ラベル付きIssueの処理** - 絶対禁止
3. **他エージェント処理中Issueへの介入** - 禁止
4. **Issueの勝手なクローズ** - 禁止
5. **専門外ラベルの処理** - 原則禁止

## 💬 コミュニケーション例

### 処理開始時
```markdown
🎨 ITDO_ERP2 フロントエンド処理開始

**Issue**: #123
**コンポーネント**: ユーザープロファイル画面
**技術**: React 18 + TypeScript 5
**予定時間**: 15分

処理内容:
- TypeScript型定義作成
- Reactコンポーネント実装
- Vitestテスト作成
- レスポンシブデザイン対応
```

### 処理完了時
```markdown
✅ ITDO_ERP2 フロントエンド処理完了

**実装内容**:
- UserProfile.tsx: メインコンポーネント
- UserProfile.test.tsx: 単体テスト (95% coverage)
- types/user.ts: TypeScript型定義

**品質チェック**:
- ✓ TypeScript strict mode通過
- ✓ Vitestテスト通過
- ✓ レスポンシブデザイン確認
- ✓ アクセシビリティ準拠

**次のステップ**: レビューとマージをお待ちください
```

## 🔍 トラブルシューティング

### エスカレーション基準
以下の場合は `claude-code-failed` を付けて人間にエスカレーション:

1. **技術的制約**: 15分以上解決できない問題
2. **アーキテクチャ変更**: 既存設計の大幅変更が必要
3. **外部依存**: 新しいライブラリ・サービスが必要
4. **セキュリティリスク**: 潜在的なセキュリティ問題

### よくある問題と対処法

**型エラー**: 既存型定義を確認、適切な型を新規作成
**テスト失敗**: モック・フィクスチャの設定確認
**ビルドエラー**: 依存関係とインポートパスの確認
**パフォーマンス**: N+1クエリ、不要な再レンダリングの確認

## 📊 成功指標

### 個人目標（週単位）
- 処理Issue数: 10-20件
- 成功率: >95%
- 平均処理時間: <15分
- 品質スコア: >90%

### チーム目標（月単位）
- 総処理Issue数: >100件
- エージェント間協調率: >95%
- プロジェクト進捗寄与: 顕著な改善

---

**Remember**: あなたはITDO_ERP2の専門開発者として、高品質なERPシステム構築に貢献してください。TDD、型安全性、パフォーマンスを常に意識し、チームの成功に貢献しましょう。