# Claude Code 開発ワークフロー

## 基本開発プロンプト

```
私はこれから Issue #[番号] の [機能名] の実装を行います。以下の手順で進めてください：

前提条件の確認:
- ハイブリッド開発環境を使用します
- データ層（PostgreSQL, Redis, Keycloak）は `podman-compose -f infra/compose-data.yaml up -d` で起動済み
- 開発はローカル環境で実行（高速開発）またはコンテナ内（環境再現時）を選択

0. **Issue確認フェーズ**
   - Issue #[番号] の内容を確認し、要件を理解してください
   - 不明点があれば質問してください
   - 関連するIssueやPRがないか確認してください

1. **Draft PR作成フェーズ**
   - ローカルで feature/#[Issue番号]-[簡潔な説明] ブランチを作成
   - Draft PRを作成: `[WIP] feat: [機能名] (Closes #[Issue番号])`
   - PRに実装計画をコメントとして記載

2. **仕様書作成フェーズ**
   - 実装する機能の詳細仕様書を作成してください
   - 仕様書には以下を含めてください：
     * 機能概要
     * インターフェース定義（API仕様/コンポーネント仕様）
     * データモデル
     * エラーハンドリング仕様
     * セキュリティ考慮事項
   - 仕様書はPRにコメントとして追加

3. **テスト仕様作成フェーズ**
   - 仕様書に基づいて、テスト仕様書を作成してください
   - 以下のテストケースを含めてください：
     * 単体テストケース（正常系・異常系）
     * 統合テストケース
     * E2Eテストシナリオ
   - 各テストケースには期待値を明記してください

4. **テストコード実装フェーズ**
   - テスト仕様に基づいて、テストコードを先に実装してください
   - Pythonの場合: pytest を使用（`cd backend && uv run pytest` で実行）
   - TypeScriptの場合: vitest を使用（`cd frontend && npm test` で実行）
   - E2Eの場合: Playwright を使用
   - テストコードをコミット・プッシュ

5. **実装フェーズ**
   - テストが失敗することを確認してから、実装を開始してください
   - 実装は小さなステップで進め、各ステップでテストを実行してください
   - ローカル開発の場合:
     * Backend: `cd backend && uv run uvicorn app.main:app --reload`
     * Frontend: `cd frontend && npm run dev`
   - すべてのテストが通ることを確認してください
   - 定期的にコミット・プッシュしてPRを更新

6. **ドキュメント更新フェーズ**
   - 実装完了後、関連ドキュメントを更新してください
   - APIドキュメント、コンポーネントドキュメントなど

7. **レビュー準備フェーズ**
   - セルフレビューを実施
   - PR descriptionを最終化
   - Draft状態を解除してReady for reviewに変更

重要な制約事項：
- データ層は必ずコンテナで実行（PostgreSQL, Redis, Keycloak）
- 開発層はローカル実行を推奨（高速な反復開発）
- 必ずIssueを起点とし、Draft PRを早期に作成すること
- テストコードを書かずに実装を進めることは禁止です
- テストが通らないコードをコミットすることは禁止です
- 型定義は必須です（Python: typing, TypeScript: 明示的な型）
  - Pythonは mypy --strict でエラーなし
  - TypeScriptは tsc --noEmit でエラーなし
  - any型の使用は原則禁止
- エラーハンドリングは必須です
- WIP状態を明確にし、作業の重複を防ぐこと

開発コマンド例:
【ローカル開発（推奨）】
- データ層起動: `podman-compose -f infra/compose-data.yaml up -d`
- Backend開発: `cd backend && uv run uvicorn app.main:app --reload`
- Frontend開発: `cd frontend && npm run dev`
- テスト実行: `cd backend && uv run pytest`
- 型チェック: `cd backend && uv run mypy --strict .`

【フルコンテナ開発（環境再現時）】
- 全環境起動: `podman-compose -f infra/compose-dev.yaml up -d`
- コンテナ接続: `podman exec -it myapp-dev-workspace bash`
- 開発サーバー: `make dev` (コンテナ内)
```

## 品質チェックリスト

### コード品質
- [ ] 型チェックが通る（mypy --strict / tsc --noEmit）
- [ ] リントエラーがない（black, isort, eslint）
- [ ] テストが全て通る
- [ ] テストカバレッジ 80%以上
- [ ] any型を使用していない

### セキュリティ
- [ ] SQLインジェクション対策済み
- [ ] XSS対策済み
- [ ] 認証・認可の実装
- [ ] 機密情報の適切な管理

### パフォーマンス
- [ ] API応答時間 200ms以内
- [ ] データベースクエリの最適化
- [ ] フロントエンドのバンドルサイズ最適化

### ドキュメント
- [ ] API仕様書の更新
- [ ] コンポーネント仕様書の更新
- [ ] README更新（必要に応じて）

## エラー対応

### よくあるエラーと対処法

#### Python関連
```bash
# uv関連エラー
export PATH="$HOME/.local/bin:$PATH"

# SQLAlchemy関連エラー
# BaseSettingsはpydantic_settingsからインポート
from pydantic_settings import BaseSettings

# Pydantic v2対応
# PostgresDsn.buildは使用せず文字列結合を使用
```

#### Frontend関連
```bash
# TailwindCSS設定
npm install -D tailwindcss postcss autoprefixer

# React Query移行
# react-query → @tanstack/react-query
npm install @tanstack/react-query
```

#### コンテナ関連
```bash
# Podmanでのイメージプル
# 完全修飾名を使用: docker.io/postgres:15-alpine

# podman-compose インストール
uv tool install podman-compose
```

## デバッグ手順

1. **ログ確認**
   ```bash
   # コンテナログ
   podman-compose -f infra/compose-data.yaml logs

   # アプリケーションログ
   tail -f backend/logs/app.log
   ```

2. **テスト実行**
   ```bash
   # Backend単体テスト
   cd backend && uv run pytest -v

   # Frontend単体テスト
   cd frontend && npm test

   # E2Eテスト
   cd e2e && npx playwright test
   ```

3. **型チェック**
   ```bash
   # Python型チェック
   cd backend && uv run mypy --strict .

   # TypeScript型チェック
   cd frontend && npm run typecheck
   ```