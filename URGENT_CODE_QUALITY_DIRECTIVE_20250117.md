# 🚨 緊急指令 - Code Quality規定の即時適用 - 2025-01-17

## 📢 全エージェント（CC01, CC02, CC03）への緊急指示

### 🎯 本指令の目的
プロジェクトの品質向上のため、新しいCode Quality規定を**即時適用**します。
全エージェントは本指令を最優先事項として実行してください。

## ⚡ 即時実行事項

### 1. 規定文書の確認（5分以内）
以下の文書を**必ず**確認してください：
- `/PROJECT_STANDARDS.md` - プロジェクト規定
- `/CLAUDE.md` - 更新されたCode Quality指示
- `/docs/CLAUDE_CODE_QUICK_REFERENCE.md` - クイックリファレンス
- `/AGENT_MANDATORY_CHECKLIST.md` - 必須チェックリスト

### 2. 環境準備（10分以内）
```bash
# 品質チェックスクリプトの実行権限確認
chmod +x ./scripts/claude-code-quality-check.sh

# pre-commitの設定確認
cd /mnt/c/work/ITDO_ERP2
uv run pre-commit install

# 初回品質チェック実行
./scripts/claude-code-quality-check.sh
```

### 3. 現在の作業への適用（即時）
現在進行中の作業がある場合：
1. 作業を一時停止
2. 品質チェックを実行
3. エラーがある場合は修正
4. 規定に従って作業を再開

## 📋 エージェント別指示

### CC01 - Frontend/UI担当
```bash
# TypeScript品質チェック
cd frontend
npm run lint:fix
npm run typecheck

# テンプレート確認
cat templates/claude-code-typescript-template.tsx
```

### CC02 - Backend/Integration担当
```bash
# Python品質チェック
cd backend
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .

# テンプレート確認
cat templates/claude-code-python-template.py
```

### CC03 - Infrastructure/DevOps担当
```bash
# CI/CD設定確認
cat .pre-commit-config.yaml
cat .github/workflows/ci.yml

# 品質監視スクリプト確認
./scripts/claude-code-quality-check.sh
```

## 🎯 本日の必達目標

各エージェントは以下を**本日中**に達成してください：

1. **エラー削減**
   - 最低50個のCode Qualityエラーを修正
   - 新規エラーは0個を維持

2. **規定遵守**
   - 全ての新規コードは規定に準拠
   - チェックリストの100%実施

3. **報告提出**
   - 17:00までに日次レポートを提出
   - 修正したエラー数を明記

## 📊 成功基準

- ✅ 品質チェックスクリプトが正常動作
- ✅ pre-commitが100%成功
- ✅ 新規エラー発生数: 0
- ✅ チェックリスト全項目クリア

## 🚨 重要な注意事項

1. **品質優先**: スピードより品質を優先
2. **段階的修正**: 一度に大量修正せず、確実に進める
3. **相互確認**: 不明点は他エージェントと確認
4. **記録保持**: 全ての修正を記録

## 💪 メッセージ

CC01, CC02, CC03の皆様へ

Code Qualityの徹底は、プロジェクト成功の基盤です。
本規定の適用により、技術的債務を解消し、
持続可能な開発体制を確立します。

各エージェントの専門性を活かし、
高品質なコードベースを実現しましょう。

**Quality First, Always!**

---

**発令時刻**: 2025-01-17 10:30 JST
**適用開始**: 即時
**第一回報告**: 本日17:00
**完全適用期限**: 2025-01-24

本指令は最優先事項として扱うこと。