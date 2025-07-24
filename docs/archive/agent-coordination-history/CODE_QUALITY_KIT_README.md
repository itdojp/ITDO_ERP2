# 🎁 Code Quality自動化キット

## 📋 概要

このキットは、任意のプロジェクトにCode Quality自動化システムを導入するための完全なセットです。

## 📦 キット内容

### 1. ドキュメント
- `docs/CODE_QUALITY_AUTOMATION_SYSTEM.md` - 実装ガイド
- `docs/CODE_QUALITY_ENFORCEMENT_GUIDE.md` - 運用ガイド
- `docs/CLAUDE_CODE_QUICK_REFERENCE.md` - クイックリファレンス

### 2. 設定ファイル
- `.vscode/settings.json` - VSCode設定
- `.pre-commit-config.yaml` - pre-commit設定
- `pyproject.toml` (ruff設定部分) - Python設定

### 3. スクリプト
- `scripts/claude-code-quality-check.sh` - 品質チェックスクリプト

### 4. テンプレート
- `templates/claude-code-python-template.py` - Pythonテンプレート
- `templates/claude-code-typescript-template.tsx` - TypeScriptテンプレート

### 5. 規定文書
- `PROJECT_STANDARDS.md` - プロジェクト規定サンプル
- `AGENT_MANDATORY_CHECKLIST.md` - チェックリストサンプル

## 🚀 クイックスタート

### 1. 基本セットアップ

```bash
# キットをプロジェクトにコピー
cp -r code-quality-kit/* your-project/

# 権限設定
chmod +x your-project/scripts/*.sh

# pre-commit インストール
cd your-project
pip install pre-commit  # または uv add --dev pre-commit
pre-commit install
```

### 2. プロジェクト固有の調整

#### Python プロジェクト
```toml
# pyproject.toml に追加
[tool.ruff]
line-length = 88  # プロジェクトに応じて調整
target-version = "py311"  # Pythonバージョンを指定
```

#### TypeScript プロジェクト
```json
// .eslintrc.json を調整
{
  "extends": ["eslint:recommended"],
  "rules": {
    "max-len": ["error", { "code": 100 }]
  }
}
```

### 3. CI/CD 統合

#### GitHub Actions
```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run quality checks
        run: ./scripts/claude-code-quality-check.sh
```

## 📊 カスタマイズガイド

### 言語別設定

#### Python
- 行長: `line-length = 120` (デフォルト: 88)
- 対象バージョン: `target-version = "py39"` 
- 除外パス: `exclude = ["migrations/"]`

#### JavaScript/TypeScript
- 使用するフォーマッター: Prettier vs ESLint
- フレームワーク別設定: React, Vue, Angular

### 厳格度の調整

#### 緩い設定（既存プロジェクト向け）
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-zero]  # エラーでも続行
```

#### 厳格な設定（新規プロジェクト向け）
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
        args: [--check]  # フォーマット違反で失敗
```

## 🔍 導入チェックリスト

- [ ] VSCode設定ファイルをコピー
- [ ] pre-commit設定をコピー・調整
- [ ] 品質チェックスクリプトをコピー
- [ ] テンプレートファイルをコピー
- [ ] プロジェクト規定を作成
- [ ] CI/CDパイプラインに統合
- [ ] チーム全員に周知
- [ ] 初回の品質チェック実行

## 📈 期待される効果

1. **即効性**: 導入直後からエラー削減
2. **継続性**: 自動化により品質維持
3. **生産性**: レビュー時間短縮
4. **学習効果**: 開発者のスキル向上

## 🆘 サポート

問題が発生した場合は、以下を確認：
1. `docs/CODE_QUALITY_AUTOMATION_SYSTEM.md` のトラブルシューティング
2. 各ツールの公式ドキュメント
3. プロジェクト固有の設定確認

## 📄 ライセンス

このキットはMITライセンスで提供されます。
自由に使用・改変・再配布可能です。

---

**Version**: 1.0.0
**Last Updated**: 2025-01-17
**Tested with**: Python 3.11+, Node.js 18+