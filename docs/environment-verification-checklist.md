# 開発環境動作確認チェックリスト

## 概要
ITDO_ERP2プロジェクトの開発環境が正しく動作することを確認するための包括的なチェックリストです。

## 1. Claude Code動作確認

### 1.1 設定ファイル読み込み確認
```bash
# Claude Codeを起動して以下のプロンプトで確認
```

**確認プロンプト:**
```
CLAUDE.mdファイルの内容を確認してください。また、.claude/ディレクトリ内の以下のファイルの内容を要約してください：
- PROJECT_CONTEXT.md
- DEVELOPMENT_WORKFLOW.md
- CODING_STANDARDS.md
- TECHNICAL_CONSTRAINTS.md
```

**期待される結果:**
- [ ] CLAUDE.mdの内容が正しく読み込まれる
- [ ] 各設定ファイルの要約が表示される
- [ ] 必須制約（TDD、型安全性など）が認識されている

### 1.2 開発ワークフロー遵守確認
**確認プロンプト:**
```
仮のIssue #999として、ユーザー認証機能の実装を8フェーズの開発ワークフローに従って計画してください。実際のコードは書かず、各フェーズで何を行うかを説明してください。
```

**期待される結果:**
- [ ] 8フェーズすべてが順番に言及される
- [ ] TDDアプローチが明確に示される
- [ ] ドラフトPR作成が含まれる

### 1.3 制約事項の遵守確認
**確認プロンプト:**
```
backend/app/models/にuser.pyファイルを作成して、Userモデルのスケルトンを実装してください。ただし、実装前にテストファイルの作成を求めてください。
```

**期待される結果:**
- [ ] テストファイルの作成を先に提案する
- [ ] 型安全性（no any）が守られる
- [ ] SQLAlchemyとPydanticの使用

## 2. 開発環境動作確認

### 2.1 基本ツール確認
```bash
# 各ツールのバージョン確認
uv --version
node --version
npm --version
podman --version
git --version
```

**チェックリスト:**
- [ ] uv 0.5.0以上がインストールされている
- [ ] Node.js 18以上がインストールされている
- [ ] npm 9以上がインストールされている
- [ ] Podman 4以上がインストールされている
- [ ] Git 2.30以上がインストールされている

### 2.2 データ層起動確認
```bash
# データ層の起動
make start-data

# 起動確認（別ターミナル）
make status
```

**チェックリスト:**
- [ ] PostgreSQLコンテナが起動（5432ポート）
- [ ] Redisコンテナが起動（6379ポート）
- [ ] Keycloakコンテナが起動（8080ポート）
- [ ] PgAdminコンテナが起動（5050ポート）

**接続確認:**
```bash
# PostgreSQL接続テスト
PGPASSWORD=itdo_password psql -h localhost -U itdo_user -d itdo_erp -c "SELECT version();"

# Redis接続テスト
redis-cli -h localhost ping
```

### 2.3 バックエンド環境確認
```bash
cd backend

# 仮想環境作成と依存関係インストール
uv venv
uv pip sync requirements-dev.txt

# 開発サーバー起動
uv run uvicorn app.main:app --reload
```

**チェックリスト:**
- [ ] 仮想環境が正常に作成される
- [ ] 依存関係がエラーなくインストールされる
- [ ] サーバーがhttp://localhost:8000で起動
- [ ] /docsでSwagger UIが表示される
- [ ] /healthエンドポイントが{"status":"healthy"}を返す

### 2.4 フロントエンド環境確認
```bash
cd frontend

# 依存関係インストール
npm ci

# 開発サーバー起動
npm run dev
```

**チェックリスト:**
- [ ] 依存関係がエラーなくインストールされる
- [ ] サーバーがhttp://localhost:3000で起動
- [ ] Reactアプリケーションが正常に表示される
- [ ] HMR（Hot Module Replacement）が動作する

### 2.5 統合動作確認
```bash
# プロジェクトルートから
make dev
```

**チェックリスト:**
- [ ] Backend/Frontendが同時に起動する
- [ ] フロントエンドからバックエンドAPIにアクセスできる
- [ ] CORSエラーが発生しない

## 3. テスト環境動作確認

### 3.1 バックエンドテスト
```bash
cd backend

# 型チェック
uv run mypy --strict app/

# リント
uv run ruff check app/
uv run ruff format --check app/

# ユニットテスト
uv run pytest tests/ -v

# カバレッジ付きテスト
uv run pytest tests/ -v --cov=app --cov-report=html
```

**チェックリスト:**
- [ ] 型チェックがエラーなく完了
- [ ] リントチェックがパス
- [ ] フォーマットチェックがパス
- [ ] テストが実行される（初期は0件でもOK）
- [ ] カバレッジレポートが生成される

### 3.2 フロントエンドテスト
```bash
cd frontend

# 型チェック
npm run typecheck

# リント
npm run lint

# テスト
npm test

# カバレッジ付きテスト
npm run coverage
```

**チェックリスト:**
- [ ] TypeScript型チェックがパス
- [ ] ESLintがパス
- [ ] テストが実行される
- [ ] カバレッジレポートが生成される

### 3.3 統合テストスクリプト
```bash
# プロジェクトルートから
./scripts/test.sh --no-e2e
```

**チェックリスト:**
- [ ] スクリプトが正常に実行される
- [ ] バックエンド/フロントエンド両方のテストが実行される
- [ ] レポートがtest-reports/に生成される

## 4. GitHub Actions動作確認

### 4.1 ローカルでのActions確認（act使用）
```bash
# actのインストール（未インストールの場合）
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# CI workflowのテスト
act -W .github/workflows/ci.yml

# 型チェックworkflowのテスト
act -W .github/workflows/typecheck.yml
```

### 4.2 GitHubでの動作確認

**プルリクエスト作成によるテスト:**
```bash
# テストブランチ作成
git checkout -b test/ci-verification

# 軽微な変更を加える
echo "# CI Test" >> README.md
git add README.md
git commit -m "test: Verify CI pipeline"

# プッシュしてPR作成
git push origin test/ci-verification
```

**確認項目:**
- [ ] CI workflowが自動的にトリガーされる
- [ ] Type Check workflowが実行される
- [ ] Security Scan workflowが実行される
- [ ] Auto Review Requestが動作する
- [ ] 全てのチェックがパスする（初期状態）

### 4.3 Pre-commitフック確認
```bash
# pre-commitのセットアップ
make pre-commit

# テストコミット
echo "test_var: str = 'test'" >> backend/app/test_file.py
git add backend/app/test_file.py
git commit -m "test: Pre-commit hook"
```

**チェックリスト:**
- [ ] pre-commitフックが実行される
- [ ] 各種チェックが自動実行される
- [ ] 問題があれば自動修正される

## 5. セキュリティ設定確認

### 5.1 シークレット検出
```bash
# テスト用シークレットを含むファイル作成
echo "API_KEY=sk-1234567890abcdef" > test_secret.txt
git add test_secret.txt
git commit -m "test: Secret detection"
```

**期待される結果:**
- [ ] pre-commitがシークレットを検出してブロック
- [ ] コミットが失敗する

```bash
# クリーンアップ
rm test_secret.txt
git reset HEAD
```

### 5.2 セキュリティスキャン
```bash
make security-scan
```

**チェックリスト:**
- [ ] Banditが実行される（Python）
- [ ] Safetyが実行される（Python依存関係）
- [ ] npm auditが実行される（Node.js）

## 6. 開発ワークフロー確認

### 6.1 新機能開発シミュレーション
1. **Issue作成**
   - GitHubで新しいIssueを作成
   - ラベル付け（enhancement）

2. **開発開始**
   ```bash
   # ブランチ作成
   git checkout -b feature/issue-1-test-feature
   
   # ドラフトPR作成用の空コミット
   git commit --allow-empty -m "feat: [WIP] Test feature #1"
   git push origin feature/issue-1-test-feature
   ```

3. **テスト作成**
   ```bash
   # バックエンドテスト作成
   touch backend/tests/test_example.py
   
   # フロントエンドテスト作成
   touch frontend/src/components/Example.test.tsx
   ```

4. **実装**
   - テストを書いてから実装

5. **確認**
   ```bash
   make test
   make lint
   make typecheck
   ```

**チェックリスト:**
- [ ] ブランチ戦略が機能する
- [ ] GitHub Actionsが各プッシュで動作
- [ ] レビュアーが自動アサインされる

## 7. Makefile コマンド確認

各コマンドの動作確認:

```bash
make help          # ヘルプ表示
make setup-dev     # 開発環境セットアップ
make dev           # 開発サーバー起動
make test          # 基本テスト
make test-full     # 包括的テスト
make lint          # リント実行
make typecheck     # 型チェック
make security-scan # セキュリティスキャン
make build         # コンテナビルド
make clean         # クリーンアップ
```

**チェックリスト:**
- [ ] 各コマンドが正常に動作する
- [ ] エラーメッセージが適切
- [ ] 並列実行が機能する（make dev）

## 8. コンテナビルド確認

### 8.1 バックエンドコンテナ
```bash
cd backend
docker build -t itdo-erp-backend:test .
docker run --rm -p 8001:8000 itdo-erp-backend:test
```

**チェックリスト:**
- [ ] ビルドが成功する
- [ ] コンテナが起動する
- [ ] ヘルスチェックが機能する

### 8.2 フロントエンドコンテナ
```bash
cd frontend
docker build -t itdo-erp-frontend:test .
docker run --rm -p 8081:80 itdo-erp-frontend:test
```

**チェックリスト:**
- [ ] ビルドが成功する
- [ ] Nginxが正常に起動する
- [ ] 静的ファイルが提供される

## 9. 統合確認

### 9.1 フルスタック動作
```bash
# すべてのサービスを起動
make start-data
make dev

# 別ターミナルで確認
curl http://localhost:8000/health
curl http://localhost:3000
```

### 9.2 開発フロー全体
1. Issueからブランチ作成
2. TDDでの開発
3. ローカルテスト実行
4. PR作成
5. CI/CDパイプライン通過
6. レビュー＆マージ

## 10. トラブルシューティング確認

一般的な問題が解決できることを確認:

- [ ] ポート競合の解決
- [ ] 依存関係の再インストール
- [ ] キャッシュクリア
- [ ] 環境変数の設定

## 確認完了基準

以下がすべて確認できれば、開発環境は正常に動作しています：

1. **Claude Code**: 設定ファイルを認識し、制約を遵守
2. **ローカル開発環境**: すべてのサービスが起動・連携
3. **テスト環境**: 各種テストツールが動作
4. **CI/CD**: GitHub Actionsが正常に実行
5. **セキュリティ**: 各種チェックが機能
6. **開発フロー**: Issue駆動開発が実践可能

## 次のステップ

環境確認が完了したら：

1. 実際の機能開発を開始
2. チーム固有のカスタマイズを追加
3. 本番環境へのデプロイ準備
4. ドキュメントの継続的な更新