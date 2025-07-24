# 🚨 CC01, CC02, CC03 - 即時実行指令

## 📢 最優先タスク

### 全エージェント共通：以下のURLから指示を確認してください

**メイン指示文書（必読）**:
https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/AGENT_CODE_QUALITY_DIRECTIVE_GITHUB_20250117.md

**クイックスタートガイド**:
https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/AGENT_QUICK_START_CODE_QUALITY.md

## ⚡ 30秒で開始

```bash
# 1. 指示を確認
curl -s https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/AGENT_QUICK_START_CODE_QUALITY.md

# 2. ツールを入手
wget https://raw.githubusercontent.com/itdojp/ITDO_ERP2/feature/issue-160-ui-component-design-requirements/scripts/claude-code-quality-check.sh
chmod +x claude-code-quality-check.sh

# 3. 実行
./claude-code-quality-check.sh
```

## 🎯 役割別タスク

### CC01 - Frontend
- TypeScriptテンプレートを使用
- `npm run lint:fix`を実行
- 新規エラー0個を維持

### CC02 - Backend  
- Pythonテンプレートを使用
- `uv run ruff format .`を実行
- 既存エラーを50個以上修正

### CC03 - Infrastructure
- 品質チェックスクリプトで全体監視
- メトリクスレポート作成
- CI/CD統合確認

## 📊 報告事項（17:00まで）

```yaml
エージェント: CC0X
日付: 2025-01-17
実施内容:
  - テンプレート使用: Yes/No
  - 修正エラー数: X個
  - 新規エラー: 0個（必須）
  - pre-commit成功: 100%
```

---

**開始時刻**: 即時
**PR #171参照**: https://github.com/itdojp/ITDO_ERP2/pull/171