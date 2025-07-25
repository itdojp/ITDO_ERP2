# 🛡️ Code Quality自動化システム - 実装ガイド

## 📋 概要

本ドキュメントは、Claude Codeエージェントと人間の開発者が協働する環境において、Code Qualityを自動的に維持するシステムの実装方法を説明します。このシステムは他のプロジェクトでも再利用可能です。

## 🎯 システムの目的

1. **エラーの事前防止**: コード作成時点でのエラー回避
2. **自動修正**: 検出されたエラーの自動修正
3. **品質の可視化**: メトリクスによる品質管理
4. **エージェント対応**: AI開発者にも適用可能な仕組み

## 🏗️ システム構成

### 1. 3層防御アーキテクチャ

```
┌─────────────────┐
│  開発時（IDE）   │ ← リアルタイム検出
├─────────────────┤
│ コミット時      │ ← pre-commit hook
├─────────────────┤
│  PR/CI時        │ ← GitHub Actions
└─────────────────┘
```

### 2. 必要なコンポーネント

- **リンター/フォーマッター**: ruff (Python), ESLint (TypeScript)
- **型チェッカー**: mypy (Python), tsc (TypeScript)
- **pre-commit**: マルチ言語対応のGitフック管理
- **自動化スクリプト**: 品質チェックの一括実行

## 📁 ファイル構成

```
project-root/
├── .vscode/
│   └── settings.json          # IDE設定
├── .pre-commit-config.yaml    # pre-commit設定
├── docs/
│   ├── CODE_QUALITY_ENFORCEMENT_GUIDE.md
│   └── CLAUDE_CODE_QUICK_REFERENCE.md
├── scripts/
│   └── claude-code-quality-check.sh
├── templates/
│   ├── claude-code-python-template.py
│   └── claude-code-typescript-template.tsx
├── PROJECT_STANDARDS.md       # プロジェクト規定
├── AGENT_MANDATORY_CHECKLIST.md
└── CLAUDE.md                  # AI向け指示
```

## 🚀 実装手順

### Step 1: IDE設定 (VSCode)

`.vscode/settings.json`:
```json
{
  // Python設定
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.ruffArgs": [
    "--line-length=88",
    "--select=E,F,I,N,W",
    "--fix"
  ],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.rulers": [88]
  },
  
  // TypeScript設定
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  
  // 共通設定
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

### Step 2: pre-commit設定

`.pre-commit-config.yaml`:
```yaml
repos:
  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # TypeScript
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.17.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$

  # 共通
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
```

### Step 3: 自動チェックスクリプト

`scripts/claude-code-quality-check.sh`:
```bash
#!/bin/bash
set -e

echo "🤖 Code Quality Check Starting..."

# Python Check
if [ -d "backend" ]; then
    cd backend
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    cd ..
fi

# TypeScript Check
if [ -d "frontend" ]; then
    cd frontend
    npm run lint:fix
    cd ..
fi

# Pre-commit
uv run pre-commit run --all-files || echo "⚠️  Some checks failed"

echo "✅ Quality Check Complete!"
```

### Step 4: テンプレートファイル

開発者が新規ファイル作成時に使用するベーステンプレートを用意します。

### Step 5: プロジェクト規定

`PROJECT_STANDARDS.md`で以下を定義：
- Code Qualityメトリクス目標
- 必須開発フロー
- コーディング規約
- エージェント別責任範囲

## 📊 メトリクス管理

### 目標設定例
| メトリクス | 目標値 | 測定方法 |
|-----------|--------|----------|
| 新規エラー発生率 | 0個/週 | CI/CDログ |
| pre-commit成功率 | 100% | Git履歴 |
| 型カバレッジ | >95% | mypy/tsc |

### 監視スクリプト
```bash
# エラー数カウント
cd backend && uv run ruff check . | wc -l
cd frontend && npm run lint 2>&1 | grep error | wc -l
```

## 🤖 Claude Code対応

### CLAUDE.md への追記
```markdown
8. **MANDATORY - Code Quality Standards**: 
   - **BEFORE writing code**: Check with `./scripts/claude-code-quality-check.sh`
   - **AFTER writing code**: Format with `uv run ruff format .`
   - **BEFORE committing**: Run `uv run pre-commit run --all-files`
```

### エージェント用チェックリスト
作業の各段階で確認すべき項目を明確化し、品質を保証します。

## 🔧 トラブルシューティング

### よくある問題と対処法

1. **大量のエラーが既に存在する場合**
   ```bash
   # 段階的修正
   uv run ruff check . --select E501 --fix  # 行長のみ
   uv run ruff check . --select F401 --fix  # インポートのみ
   ```

2. **pre-commitが遅い場合**
   ```yaml
   # 特定のフックを無効化
   skip: [mypy]  # 開発中は型チェックをスキップ
   ```

3. **エージェントが規定を守らない場合**
   - Git hookで強制的にブロック
   - CI/CDでPRをマージ不可に

## 📈 導入効果の測定

### Before/After比較
- エラー数の推移グラフ
- 開発速度の変化
- レビュー時間の短縮

### ROI計算
- エラー修正時間の削減
- 品質起因の障害減少
- 開発者満足度向上

## 🎯 成功のポイント

1. **段階的導入**: 全てを一度に適用せず段階的に
2. **自動化優先**: 手動チェックは最小限に
3. **可視化**: メトリクスをダッシュボード化
4. **教育**: 開発者への継続的な啓蒙

## 📚 参考資料

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [ESLint Documentation](https://eslint.org/docs/)
- [pre-commit Documentation](https://pre-commit.com/)

---

本システムを導入することで、Code Qualityの自動維持が可能になり、
開発効率と品質の両立を実現できます。