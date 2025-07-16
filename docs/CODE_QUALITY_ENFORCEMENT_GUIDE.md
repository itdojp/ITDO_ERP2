# 📚 Code Quality自動化ガイド

## 🎯 目的
開発段階でCode Qualityエラーを防ぎ、CI/CDでのエラーを未然に防ぐ

## 🛡️ 3層防御システム

### 1️⃣ **開発時（リアルタイム）**
VSCodeの設定により、コーディング中に即座にエラーを検出・修正

**設定済み機能**:
- 保存時の自動フォーマット
- インポート文の自動整理
- 行長制限の視覚的表示（88文字）
- 未使用インポートの自動削除

### 2️⃣ **コミット時（pre-commit）**
コミット前に自動的にコード品質をチェック・修正

**実行されるチェック**:
```bash
# pre-commitのセットアップ
cd backend
uv run pre-commit install

# 手動実行（全ファイル）
uv run pre-commit run --all-files
```

### 3️⃣ **PR作成時（CI/CD）**
GitHub ActionsでPR時に最終チェック

## 📋 主要なCode Qualityルール

### Python（ruff）
```python
# ❌ 避けるべきコード
import os, sys  # E401: 複数インポート
def function_with_very_long_name_that_exceeds_the_88_character_limit_and_causes_E501_error():  # E501: 行長超過
    pass
import unused_module  # F401: 未使用インポート

# ✅ 推奨コード
import os
import sys

def function_with_short_name():
    """短く明確な関数名を使用"""
    pass
```

### TypeScript（ESLint）
```typescript
// ❌ 避けるべきコード
const data: any = fetchData();  // any型の使用
console.log("debug");  // console.logの残存

// ✅ 推奨コード
interface UserData {
  id: string;
  name: string;
}
const data: UserData = fetchData();
```

## 🚀 導入手順

### 1. VSCode拡張機能のインストール
- Python: `charliermarsh.ruff`
- TypeScript: `dbaeumer.vscode-eslint`
- Prettier: `esbenp.prettier-vscode`

### 2. pre-commitの有効化
```bash
# 初回セットアップ
cd /mnt/c/work/ITDO_ERP2
uv run pre-commit install

# 既存ファイルの一括修正
uv run pre-commit run --all-files
```

### 3. GitHub Branch Protection設定
mainブランチで以下を有効化:
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Include administrators

## 🔧 トラブルシューティング

### ruffエラーが大量に出る場合
```bash
# 自動修正可能なエラーを一括修正
cd backend
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .
```

### pre-commitが失敗する場合
```bash
# スキップして後で修正（緊急時のみ）
git commit --no-verify -m "fix: urgent fix"

# 後で必ず修正
uv run pre-commit run --all-files
```

## 📈 効果測定

導入前後の比較:
- **導入前**: 244個のCode Qualityエラー
- **導入後目標**: 新規エラー0個/週

## 🎯 ベストプラクティス

1. **小さく頻繁にコミット**: エラーの蓄積を防ぐ
2. **PR作成前に確認**: `uv run pre-commit run --all-files`
3. **CI失敗時は即修正**: 技術的債務を溜めない
4. **チーム全体で徹底**: 全員が同じ設定を使用

---

これらの仕組みにより、Code Qualityエラーの発生を根本的に防ぎ、
開発効率と品質を大幅に向上させることができます。