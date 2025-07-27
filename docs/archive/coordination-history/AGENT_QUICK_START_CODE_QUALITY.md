# 🚀 Code Quality クイックスタート（エージェント用）

## 📋 5分で始めるCode Quality

### 1️⃣ 必須文書を確認（GitHub）
```bash
# プロジェクト規定を読む
curl -s https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/PROJECT_STANDARDS.md | less

# チェックリストを確認
curl -s https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/AGENT_MANDATORY_CHECKLIST.md | less
```

### 2️⃣ 品質チェックツールを入手
```bash
# 品質チェックスクリプト
wget https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/scripts/claude-code-quality-check.sh
chmod +x claude-code-quality-check.sh

# テンプレート（Python）
wget https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/templates/claude-code-python-template.py

# テンプレート（TypeScript）
wget https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/templates/claude-code-typescript-template.tsx
```

### 3️⃣ 基本コマンド（暗記必須）

#### Python作業時
```bash
# 作業前
cd backend && uv run ruff check . | head -20

# 作業後
cd backend && uv run ruff check . --fix
cd backend && uv run ruff format .

# コミット前
uv run pre-commit run --all-files
```

#### TypeScript作業時
```bash
# 作業前
cd frontend && npm run lint

# 作業後  
cd frontend && npm run lint:fix

# コミット前
uv run pre-commit run --all-files
```

## 🎯 今すぐやること

### CC01（Frontend）
```bash
# 1. テンプレートで新規コンポーネント作成
cp claude-code-typescript-template.tsx frontend/src/components/NewFeature.tsx

# 2. 既存ファイルの修正
cd frontend && npm run lint:fix
```

### CC02（Backend）
```bash
# 1. テンプレートで新規サービス作成
cp claude-code-python-template.py backend/app/services/new_service.py

# 2. エラー修正
cd backend && uv run ruff check . --fix --unsafe-fixes
```

### CC03（Infrastructure）
```bash
# 1. 全体チェック実行
./claude-code-quality-check.sh

# 2. 結果をレポート
echo "Total Python errors: $(cd backend && uv run ruff check . 2>/dev/null | wc -l)"
```

## 📊 成功の定義

- ✅ 新規ファイル = テンプレート使用
- ✅ 編集後 = 必ずformat実行
- ✅ エラー数 = 0個維持

## 🔗 詳細情報

完全版ドキュメント:
https://github.com/itdojp/ITDO_ERP2/pull/171

---

**Remember**: Quality First, Always!