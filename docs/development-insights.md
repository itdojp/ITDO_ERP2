# 開発環境構築で得られた知見

## 概要
ITDO_ERP2プロジェクトの開発環境構築作業（2025年1月）で得られた技術的知見と解決策をまとめています。

## 1. パッケージマネージャーの移行

### 問題: Pydantic v2への移行
**エラー内容:**
```python
ImportError: cannot import name 'BaseSettings' from 'pydantic'
```

**解決策:**
```python
# 旧: pydantic v1
from pydantic import BaseSettings

# 新: pydantic v2
from pydantic_settings import BaseSettings
```

**追加の変更点:**
- `PostgresDsn.build()` メソッドが廃止されたため、文字列連結で対応
- バリデーターの書き方が変更（`@validator` → `@field_validator`）

### 問題: React Queryのパッケージ名変更
**エラー内容:**
```
npm ERR! 404 Not Found - GET https://registry.npmjs.org/react-query - Not found
```

**解決策:**
```json
// 旧
"react-query": "^3.39.0"

// 新
"@tanstack/react-query": "^5.0.0"
```

## 2. Pythonパッケージ管理

### uvツールの採用
**利点:**
- 高速なパッケージインストール（Rustベース）
- 統一されたツールチェイン
- 仮想環境の自動管理

**使用方法:**
```bash
# インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境作成と依存関係インストール
uv venv
uv pip sync requirements.txt

# 実行
uv run python script.py
```

### pyproject.tomlの設定
**問題:** hatchlingビルドシステムでのホイール生成エラー

**解決策:**
```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

## 3. コンテナレジストリの指定

### Podmanでのイメージ解決問題
**問題:** 
```
Error: short-name "postgres:15-alpine" did not resolve to an alias
```

**解決策:** 完全修飾イメージ名を使用
```yaml
# 旧
image: postgres:15-alpine

# 新
image: docker.io/postgres:15-alpine
```

## 4. Claude Code統合のベストプラクティス

### CLAUDE.mdファイルの構成
1. **必須読み込みファイルの明記**
   - プロジェクトコンテキスト
   - 開発ワークフロー
   - コーディング標準
   - 技術的制約

2. **制約事項の強調**
   - TDD必須
   - 型安全性の厳格化
   - ハイブリッド環境の推奨

3. **プロンプトテンプレートの提供**
   - 一貫した開発アプローチ
   - 必要なファイルの読み込み指示

### .claudeディレクトリの活用
```
.claude/
├── PROJECT_CONTEXT.md      # ビジネスドメイン知識
├── DEVELOPMENT_WORKFLOW.md  # 8フェーズ開発プロセス
├── CODING_STANDARDS.md      # 詳細なコーディング規約
└── TECHNICAL_CONSTRAINTS.md # パフォーマンス・セキュリティ要件
```

## 5. GitHub Actions設定の要点

### ワークフロー設計
1. **CI/CDパイプライン**
   - 並列実行による高速化
   - キャッシュの活用
   - マトリックステストの実装

2. **セキュリティスキャン**
   - 複数ツールの組み合わせ
   - 段階的なセキュリティレベル
   - 自動修正の提案

3. **型チェック**
   - 最も厳格な設定（`--strict`）
   - エラーと警告の分離
   - 段階的な適用

### パフォーマンス最適化
```yaml
# 並列ジョブ実行
strategy:
  matrix:
    python-version: [3.13, 3.12]
    
# 依存関係キャッシュ
- uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/requirements*.txt') }}
```

## 6. 開発環境の自動化

### Makefileの活用
```makefile
# 複数プロセスの同時起動
dev:
	@(cd backend && uv run uvicorn app.main:app --reload) & \
	(cd frontend && npm run dev) & \
	wait
```

### スクリプトの構造化
1. **エラーハンドリング**
   - `set -e` で即座に停止
   - 色付き出力で視認性向上
   - 詳細なエラーメッセージ

2. **環境検出**
   - コンテナ/ローカルの自動判定
   - 必要なツールの存在確認
   - サービスの起動状態チェック

## 7. テスト戦略

### 包括的テストスクリプト
```bash
# オプション別実行
./scripts/test.sh --backend-only   # バックエンドのみ
./scripts/test.sh --no-e2e         # E2Eテストを除外
./scripts/test.sh                  # フルテスト
```

### カバレッジレポート
- HTMLレポートの自動生成
- 複数形式での出力
- CI/CDでの自動アップロード

## 8. セキュリティ考慮事項

### シークレット管理
1. **detect-secretsの導入**
   - ベースライン設定
   - pre-commitフック統合
   - 定期的なスキャン

2. **環境変数の分離**
   - `.env.example` の提供
   - 本番環境変数の暗号化
   - GitHub Secretsの活用

### コンテナセキュリティ
```dockerfile
# 非rootユーザーの使用
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# ヘルスチェックの実装
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1
```

## 9. 推奨される開発フロー

### 日次開発サイクル
1. **朝の環境準備**
   ```bash
   make start-data     # データ層起動
   make dev           # 開発サーバー起動
   ```

2. **開発中**
   - TDDサイクルの実践
   - 頻繁なコミット
   - pre-commitフックの活用

3. **終了時**
   ```bash
   make test          # テスト実行
   make stop-data     # データ層停止
   ```

### コードレビュー準備
```bash
# 包括的チェック
make lint          # リント
make typecheck     # 型チェック
make test-full     # フルテスト
make security-scan # セキュリティスキャン
```

## 10. トラブルシューティング

### よくある問題と解決策

1. **uvコマンドが見つからない**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Podmanの権限エラー**
   ```bash
   # rootlessモードの確認
   podman system migrate
   ```

3. **ポート競合**
   ```bash
   # 使用中のポート確認
   lsof -i :8000
   lsof -i :3000
   ```

4. **依存関係の競合**
   ```bash
   # クリーンインストール
   rm -rf backend/.venv frontend/node_modules
   make setup-dev
   ```

## 11. Python 3.13移行の知見

### 移行プロセス
**実施期間:** 2025年7月

**移行理由:**
- Python 3.11から最新版への更新要望
- 最新言語機能とパフォーマンス向上の活用
- セキュリティアップデートの適用

### 移行手順
1. **影響範囲の調査**
   - 依存関係の互換性確認
   - 型チェックエラーの事前検証
   - テストスイートの動作確認

2. **段階的アップデート**
   ```bash
   # pyproject.tomlの更新
   requires-python = ">=3.13"
   
   # GitHub Actionsの更新
   python-version: [3.13]
   
   # Dockerイメージの更新
   FROM python:3.13-slim
   ```

3. **検証とテスト**
   - 全テストスイートの実行
   - 型チェック（mypy --strict）の合格
   - CI/CDパイプラインの動作確認

### 発見された課題と解決策

1. **TypeScript テストファイルの型エラー**
   ```typescript
   // 問題: vitest globals が認識されない
   describe, it, expect が未定義エラー
   
   // 解決策: tsconfig.jsonに追加
   "types": ["vitest/globals", "@testing-library/jest-dom"]
   ```

2. **Python テスト関数の型注釈不足**
   ```python
   # 問題: mypy --strict でreturn type annotation必須
   def test_function():  # エラー
   
   # 解決策: 明示的な型注釈
   def test_function() -> None:  # OK
   ```

### パフォーマンス向上の確認
- **uvツール**: Python 3.13対応により高速化
- **型チェック**: 最新mypyでの検証精度向上
- **テスト実行**: pytest最新版での安定性向上

### 移行後の効果
1. **開発効率の向上**
   - 最新IDEサポートの活用
   - より正確な型推論
   - 改善されたエラーメッセージ

2. **セキュリティの強化**
   - 最新セキュリティパッチの適用
   - 脆弱性の修正済みライブラリ使用

3. **将来性の確保**
   - 長期サポート版の利用
   - 新機能への早期対応可能

## まとめ

この開発環境構築では、モダンなツールチェインとベストプラクティスを組み合わせることで、高品質で保守性の高いシステム開発基盤を実現しました。特に以下の点が重要です：

1. **自動化の徹底** - 手動作業を最小限に
2. **型安全性の確保** - ランタイムエラーの予防
3. **セキュリティファースト** - 開発初期からのセキュリティ考慮
4. **開発者体験の向上** - 効率的なワークフローの実現
5. **継続的な技術更新** - Python 3.13移行に見る適応力

これらの知見を活用することで、今後の開発作業がより効率的かつ安全に進められることが期待されます。