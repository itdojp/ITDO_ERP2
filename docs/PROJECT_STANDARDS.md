# 📋 ITDO ERP v2 プロジェクト規定 - 2025年1月17日制定

## 🚨 必須遵守事項 - Code Quality Standards

本規定は全開発者およびClaude Codeエージェント（CC01, CC02, CC03）が**必ず遵守**する義務があります。

### ⚡ 最重要規定 - The Golden Rules

1. **コード作成前**: 必ず品質チェックを実行
   ```bash
   ./scripts/claude-code-quality-check.sh
   ```

2. **コード作成後**: 必ずフォーマットを実行
   ```bash
   cd backend && uv run ruff format .
   cd frontend && npm run lint:fix
   ```

3. **コミット前**: 必ずpre-commitを実行
   ```bash
   uv run pre-commit run --all-files
   ```

### 📊 Code Quality メトリクス目標

| 項目 | 現状 | 目標 | 期限 |
|------|------|------|------|
| Python Code Qualityエラー | 244個 | 0個 | 2025/01/24 |
| TypeScript型エラー | 未測定 | 0個 | 2025/01/24 |
| 新規エラー発生率 | - | 0個/週 | 即時適用 |
| pre-commit成功率 | - | 100% | 即時適用 |

## 🔧 必須開発フロー

### 1. 新規ファイル作成時
```bash
# Python
cp templates/claude-code-python-template.py app/path/to/new_file.py

# TypeScript/React
cp templates/claude-code-typescript-template.tsx frontend/src/components/NewComponent.tsx
```

### 2. 既存ファイル編集時
```bash
# 編集前
cd backend && uv run ruff check path/to/file.py

# 編集後
cd backend && uv run ruff check path/to/file.py --fix
cd backend && uv run ruff format path/to/file.py
```

### 3. PR作成時
```bash
# 品質チェック
./scripts/claude-code-quality-check.sh

# 問題がある場合は修正
cd backend && uv run ruff check . --fix --unsafe-fixes
cd backend && uv run ruff format .

# 再確認
uv run pre-commit run --all-files

# PR作成
gh pr create --title "fix: [Issue番号] タイトル"
```

## 📏 コーディング規約

### Python
- **行長**: 最大88文字（厳守）
- **インポート順序**: 標準→サードパーティ→ローカル
- **型アノテーション**: 全関数に必須
- **docstring**: 公開関数/クラスに必須
- **未使用インポート**: 即座に削除

### TypeScript
- **any型**: 使用禁止（unknown使用）
- **型定義**: 全てのprops/stateに必須
- **console.log**: 本番コードでは削除
- **エラーハンドリング**: try-catch必須

## 🚫 禁止事項

1. **品質チェックなしのコミット**
2. **pre-commitのスキップ** (`--no-verify`の使用)
3. **エラーを含むPRの作成**
4. **型アノテーションなしの関数追加**
5. **88文字を超える行の放置**

## 🎯 エージェント別責任範囲

### CC01 - Frontend/UI担当
- TypeScript/React品質の維持
- デザインシステムの品質保証
- フロントエンドテストの品質

### CC02 - Backend/Integration担当
- Python Code Qualityの維持
- API品質の保証
- 統合テストの品質

### CC03 - Infrastructure/DevOps担当
- CI/CD品質ゲートの管理
- 自動化スクリプトの保守
- 全体的な品質監視

## 📈 品質監視とレポート

### 日次レポート（全エージェント必須）
```yaml
日付: YYYY-MM-DD
エージェント: CC0X
作業内容:
  - 作成/編集ファイル数: X
  - 修正したエラー数: X
  - 新規発生エラー: 0（必須）
  - pre-commit成功率: 100%（必須）
```

### 週次サマリー
- 総エラー数の推移
- 品質改善の進捗
- 問題点と対策

## 🔄 規定改定

本規定は以下の場合に改定されます：
- 新技術の導入時
- 品質基準の変更時
- 四半期レビュー時

---

**制定日**: 2025年1月17日
**適用開始**: 即時
**次回レビュー**: 2025年2月17日

全エージェントは本規定を遵守し、高品質なコードベースの維持に努めること。