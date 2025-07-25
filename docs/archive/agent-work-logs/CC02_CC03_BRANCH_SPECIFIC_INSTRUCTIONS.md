# 📋 CC02, CC03 - ブランチ別状況確認と指示

## 🎯 重要な発見：ブランチ環境の違い

### 📊 状況整理
- **CC01**: `feature/issue-142-user-profile-frontend` ブランチ
  - ✅ Code Quality: 完璧（0エラー）
  - ✅ システム状態: 正常動作
  - ✅ 品質基準: 全項目達成

- **私の確認環境**: `feature/issue-160-ui-component-design-requirements` ブランチ
  - ❌ 3,023エラー（マージコンフリクト含む）
  - ❌ システム状態: 不安定

## 🔍 CC02, CC03への確認依頼

### Step 1: 作業ブランチの確認
```bash
# 現在のブランチを確認
git branch --show-current

# ブランチの品質状況を確認
cd backend && uv run ruff check . | tail -5
cd frontend && npm run lint 2>&1 | tail -5
```

### Step 2: 結果の報告
以下の形式で報告してください：

```yaml
エージェント: CC02 または CC03
現在のブランチ: [ブランチ名]
Backend エラー数: [数値]
Frontend エラー数: [数値]
マージコンフリクト: あり/なし
最新コミット: [コミットハッシュ]
作業状態: [正常/問題あり]
```

## 🎯 ブランチ別対応方針

### ケース1: クリーンなブランチの場合（CC01と同様）
```bash
# 高品質環境での作業継続
./claude-code-quality-check.sh
# テンプレート使用で新機能開発
cp templates/claude-code-python-template.py app/services/new_feature.py
```

### ケース2: 問題のあるブランチの場合
```bash
# まずマージコンフリクト解決
grep -r "<<<<<<< HEAD" . | wc -l

# エラー修正
uv run ruff check . --fix --unsafe-fixes
uv run ruff format .

# 品質向上
git add -A
git commit -m "fix: Resolve quality issues in [ブランチ名]"
```

## 📊 推奨作業順序

### CC02（Backend担当）
1. **ブランチ状況確認**
2. **エラー数が多い場合**:
   ```bash
   # 段階的修正
   uv run ruff check . --select E999  # Syntax errors first
   uv run ruff check . --select E501 --fix  # Line length
   uv run ruff check . --select F401 --fix  # Unused imports
   ```

3. **エラー数が少ない場合**:
   ```bash
   # Code Quality規定の適用
   uv run ruff format .
   # 新機能開発
   ```

### CC03（Infrastructure担当）
1. **全体状況の把握**
   ```bash
   # 全ブランチの品質確認
   git branch -a | grep -E "CC0|feature" | while read branch; do
     echo "=== $branch ==="
     git show "$branch:backend/app/main.py" > /dev/null 2>&1 && echo "Backend: OK" || echo "Backend: Missing"
   done
   ```

2. **CI/CD設定の確認**
3. **品質メトリクスの集約**

## 🏆 CC01の成功パターンを参考に

CC01が証明した要素：
- ✅ 段階的品質改善
- ✅ 徹底したエラー修正
- ✅ 継続的な品質維持
- ✅ 詳細な状況報告

## 💡 作業効率化のヒント

### 品質チェックの自動化
```bash
# Watch mode for continuous checking
watch -n 30 'cd backend && uv run ruff check . | tail -3'
```

### 成功の共有
CC01のように詳細な報告を歓迎します：
- 具体的な数値
- 改善の履歴
- 使用したコマンド
- 結果の検証方法

---

**期待する行動**:
1. ブランチ状況の即座報告
2. 環境に応じた適切な対応
3. CC01レベルの品質達成

**目標**: 全エージェントが CC01と同水準の品質環境での作業実現