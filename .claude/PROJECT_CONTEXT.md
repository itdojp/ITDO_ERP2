# プロジェクトコンテキスト

## 開発環境

### 重要: ハイブリッド開発環境
- **データ層は常にコンテナで実行**（PostgreSQL, Redis, Keycloak）
- **開発層はローカル実行を推奨**（FastAPI, React）- 開発速度優先
- **フルコンテナオプション利用可能** - 環境再現が必要な場合

### 開発構成の選択
- ローカル開発: 日常的な開発作業（高速、推奨）
- フルコンテナ: 環境依存の問題調査、本番環境の再現

## ビジネスドメイン
- 主要エンティティ: User, Organization, Project, Task
- 主要ユースケース: [具体的な業務フロー]
- ビジネスルール: [制約事項、計算ロジック]

## 技術的制約
- レスポンスタイム: API 200ms以内
- 同時接続数: 1000ユーザー
- データ保持期間: 7年

## 命名規則
- API: /api/v1/{resource}/{id}
- DB: snake_case
- Python: snake_case
- TypeScript: camelCase

## AI用メタプロンプト

あなたはこのプロジェクトの開発を支援するAIアシスタントです。
以下の原則に従って開発を進めてください：

1. **ハイブリッド開発**: データ層はコンテナ、開発層は状況に応じて選択
2. **安全第一**: テストなしでコードを書かない
3. **文書化**: 実装前に仕様を文書化
4. **一貫性**: 既存のパターンに従う
5. **効率性**: テンプレートを活用
6. **品質**: コードレビューの観点を持つ

開発環境コマンド例:

ローカル開発（推奨）:
- データ層起動: `podman-compose -f infra/compose-data.yaml up -d`
- Backend起動: `cd backend && uv run uvicorn app.main:app --reload`
- Frontend起動: `cd frontend && npm run dev`
- テスト実行: `cd backend && uv run pytest`

フルコンテナ開発（オプション）:
- コンテナ起動: `podman-compose -f infra/compose-dev.yaml up -d`
- コンテナ接続: `podman exec -it myapp-dev-workspace bash`
- 開発サーバー: `make dev` (コンテナ内で実行)

Python開発の注意事項（uvを使用）:
- 仮想環境作成: `uv venv`
- パッケージインストール: `uv pip install package-name`
- スクリプト実行: `uv run python script.py`
- テスト実行: `uv run pytest`
- **activateは使用しません** - すべて`uv run`で実行

利用可能なリソース：
- PROJECT_CONTEXT.md: ビジネスドメイン知識
- CODE_TEMPLATES/: コード生成テンプレート
- DATA_MODELS.yaml: データモデル定義
- ERROR_CATALOG.md: エラー処理パターン
- SECURITY_CHECKLIST.md: セキュリティ要件

開発時は必ず以下の順序で進めること：
1. データ層の起動確認
2. 関連ドキュメントの参照
3. テスト仕様の作成
4. テストコードの実装
5. プロダクションコードの実装
6. ドキュメントの更新