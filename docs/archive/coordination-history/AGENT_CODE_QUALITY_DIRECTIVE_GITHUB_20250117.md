# 🚨 全エージェント緊急指令 - Code Quality規定の即時適用（GitHub版）

## 📢 CC01, CC02, CC03への最優先指示

### 🎯 重要：本指令は最優先事項です

プロジェクトの品質向上のため、新しいCode Quality規定を**即時適用**します。
以下のGitHub上のドキュメントを確認し、規定に従って作業してください。

## 📚 必須確認文書（GitHub URL）

### 1. プロジェクト規定
**PROJECT_STANDARDS.md**
https://github.com/itdojp/ITDO_ERP2/blob/feature/issue-160-ui-component-design-requirements/PROJECT_STANDARDS.md

### 2. 必須チェックリスト
**AGENT_MANDATORY_CHECKLIST.md**
https://github.com/itdojp/ITDO_ERP2/blob/feature/issue-160-ui-component-design-requirements/AGENT_MANDATORY_CHECKLIST.md

### 3. クイックリファレンス
**CLAUDE_CODE_QUICK_REFERENCE.md**
https://github.com/itdojp/ITDO_ERP2/blob/feature/issue-160-ui-component-design-requirements/docs/CLAUDE_CODE_QUICK_REFERENCE.md

### 4. 実装ガイド
**CODE_QUALITY_AUTOMATION_SYSTEM.md**
https://github.com/itdojp/ITDO_ERP2/blob/feature/issue-160-ui-component-design-requirements/docs/CODE_QUALITY_AUTOMATION_SYSTEM.md

### 5. 品質チェックスクリプト
**claude-code-quality-check.sh**
https://github.com/itdojp/ITDO_ERP2/blob/feature/issue-160-ui-component-design-requirements/scripts/claude-code-quality-check.sh

## ⚡ 即時実行事項

### Step 1: 規定の確認（10分以内）
```bash
# GitHubから規定を確認
gh api repos/itdojp/ITDO_ERP2/contents/PROJECT_STANDARDS.md?ref=feature/issue-160-ui-component-design-requirements | jq -r .content | base64 -d

# チェックリストを確認
gh api repos/itdojp/ITDO_ERP2/contents/AGENT_MANDATORY_CHECKLIST.md?ref=feature/issue-160-ui-component-design-requirements | jq -r .content | base64 -d
```

### Step 2: 品質チェックスクリプトの取得と実行
```bash
# スクリプトをダウンロード
curl -o claude-code-quality-check.sh https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/scripts/claude-code-quality-check.sh
chmod +x claude-code-quality-check.sh

# 実行
./claude-code-quality-check.sh
```

### Step 3: テンプレートの活用
```bash
# Pythonテンプレート
curl -o template.py https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/templates/claude-code-python-template.py

# TypeScriptテンプレート
curl -o template.tsx https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/templates/claude-code-typescript-template.tsx
```

## 📊 必須遵守ルール

### The Golden Rules（PROJECT_STANDARDS.mdより）

1. **コード作成前**: 必ず品質チェックを実行
2. **コード作成後**: 必ずフォーマットを実行
3. **コミット前**: 必ずpre-commitを実行

### 具体的コマンド
```bash
# Python（作成前後）
cd backend && uv run ruff check . --fix
cd backend && uv run ruff format .

# TypeScript（作成前後）
cd frontend && npm run lint:fix

# コミット前
uv run pre-commit run --all-files
```

## 🎯 本日の必達目標

各エージェントは以下を**本日中**に達成：

### CC01（Frontend/UI担当）
1. TypeScriptテンプレートを使用して新規ファイルを作成
2. 既存TypeScriptファイルのCode Quality改善（最低20ファイル）
3. `npm run lint:fix`の100%成功

### CC02（Backend/Integration担当）
1. Pythonテンプレートを使用して新規ファイルを作成
2. 既存Pythonファイルのエラー修正（最低50個）
3. `uv run ruff format .`の完全実行

### CC03（Infrastructure/DevOps担当）
1. 品質チェックスクリプトの全体実行
2. CI/CDパイプラインへの品質チェック統合
3. 全体的な品質メトリクスの報告

## 📋 作業手順

### 1. 新規ファイル作成時
```bash
# テンプレートをコピー
cp template.py app/services/new_service.py
# または
cp template.tsx frontend/src/components/NewComponent.tsx

# 編集後、必ず実行
./claude-code-quality-check.sh
```

### 2. 既存ファイル編集時
```bash
# 編集前に確認
cd backend && uv run ruff check path/to/file.py

# 編集後に修正
cd backend && uv run ruff check path/to/file.py --fix
cd backend && uv run ruff format path/to/file.py
```

### 3. PR作成時
```bash
# 全体チェック
./claude-code-quality-check.sh

# エラーがある場合は修正
cd backend && uv run ruff check . --fix --unsafe-fixes

# PR作成
gh pr create --title "fix: Apply Code Quality standards"
```

## 📊 成功基準

- ✅ 品質チェックスクリプトが正常動作
- ✅ 新規エラー発生数: 0
- ✅ チェックリスト全項目クリア
- ✅ テンプレート使用率: 100%

## 💪 メッセージ

CC01, CC02, CC03の皆様へ

Code Qualityの徹底は、プロジェクト成功の基盤です。
GitHub上の規定文書を確認し、テンプレートを活用して、
高品質なコードベースを維持してください。

**Quality First, Always!**
**Use Templates, Save Time!**
**Zero New Errors!**

---

**発令時刻**: 2025-01-17 11:00 JST
**GitHub PR**: #171
**適用開始**: 即時
**報告期限**: 本日17:00