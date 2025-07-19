# 🚑 即座実行用エージェント回復プロンプト

**作成日時**: 2025年7月17日 24:05 JST  
**緊急度**: 🔴 最高緊急度  
**対象**: CC01, CC02, CC03の即座回復

## 🎯 第1次回復プロンプト (即座実行)

### 🔵 CC01用プロンプト

```
**CC01 緊急確認タスク**

以下の1つのシンプルなタスクのみを実行してください：

1. コマンド実行: `echo "CC01 Active $(date)" > CC01_STATUS.txt`
2. コミット: `git add CC01_STATUS.txt && git commit -m "CC01 recovery test"`
3. 報告: 「CC01 回復テスト完了」とコメント

**重要**: 上記以外のタスクは一切実行しないでください。
エラーがあれば具体的なメッセージを報告してください。
```

### 🔴 CC02用プロンプト

```
**CC02 緊急確認タスク**

以下の1つのシンプルなタスクのみを実行してください：

1. コマンド実行: `echo "CC02 Active $(date)" > backend/CC02_STATUS.txt`
2. コミット: `git add backend/CC02_STATUS.txt && git commit -m "CC02 recovery test"`
3. 報告: 「CC02 回復テスト完了」とコメント

**重要**: 上記以外のタスクは一切実行しないでください。
エラーがあれば具体的なメッセージを報告してください。
```

### 🔶 CC03用プロンプト

```
**CC03 緊急確認タスク**

以下の1つのシンプルなタスクのみを実行してください：

1. コマンド実行: `echo "CC03 Active $(date)" > CC03_STATUS.txt`
2. コミット: `git add CC03_STATUS.txt && git commit -m "CC03 recovery test"`
3. 報告: 「CC03 回復テスト完了」とコメント

**重要**: 上記以外のタスクは一切実行しないでください。
エラーがあれば具体的なメッセージを報告してください。
```

## 🔍 第1次効果検証方法

### 即座検証コマンド

```bash
# 30分後に実行して効果を検証
echo "=== 第1次回復テスト結果 ==="

# ファイル作成確認
echo "--- ステータスファイル確認 ---"
ls -la CC01_STATUS.txt 2>/dev/null && echo "CC01: ✅ ファイル作成成功" || echo "CC01: ❌ ファイル作成失敗"
ls -la backend/CC02_STATUS.txt 2>/dev/null && echo "CC02: ✅ ファイル作成成功" || echo "CC02: ❌ ファイル作成失敗"
ls -la CC03_STATUS.txt 2>/dev/null && echo "CC03: ✅ ファイル作成成功" || echo "CC03: ❌ ファイル作成失敗"

# コミット確認
echo "--- コミット確認 ---"
git log --oneline -5 | grep -i "recovery test" && echo "✅ 回復テストコミット確認" || echo "❌ 回復テストコミットなし"

# タイムスタンプ確認
echo "--- タイムスタンプ確認 ---"
if [ -f CC01_STATUS.txt ]; then echo "CC01: $(cat CC01_STATUS.txt)"; fi
if [ -f backend/CC02_STATUS.txt ]; then echo "CC02: $(cat backend/CC02_STATUS.txt)"; fi
if [ -f CC03_STATUS.txt ]; then echo "CC03: $(cat CC03_STATUS.txt)"; fi

echo "=== 検証完了 ==="
```

### 期待される結果

```yaml
成功ケース:
  - ファイル作成: 3件すべて成功
  - コミット: 3件すべて成功
  - エージェント報告: 3件すべて報告
  - タイムスタンプ: 現在日時が記録

部分成功ケース:
  - 1-2件のエージェントが応答
  - 応答したエージェントは次フェーズへ
  - 無応答エージェントは別アプローチ

完全失敗ケース:
  - 全エージェント無応答
  - ファイル作成なし
  - コミットなし
  - システムレベルの問題を疑う
```

## 🔄 第2次回復プロンプト (第1次成功後)

### 成功したエージェント用

#### CC01用 (第1次成功後)

```
**CC01 第2次テスト**

第1次テスト成功おめでとうございます。
次のシンプルなタスクを実行してください：

1. ディレクトリ作成: `mkdir -p frontend/src/test`
2. テストファイル作成: `echo 'export const test = "CC01 working";' > frontend/src/test/cc01-test.ts`
3. コミット: `git add frontend/src/test/ && git commit -m "CC01 phase 2 test"`
4. 報告: 「CC01 第2次テスト完了」とコメント

エラーがあれば具体的なメッセージを報告してください。
```

#### CC02用 (第1次成功後)

```
**CC02 第2次テスト**

第1次テスト成功おめでとうございます。
次のシンプルなタスクを実行してください：

1. テストファイル作成: `echo 'def test_cc02(): return "CC02 working"' > backend/test_cc02.py`
2. テスト実行: `cd backend && python test_cc02.py`
3. 結果報告: 実行結果を報告
4. コミット: `git add backend/test_cc02.py && git commit -m "CC02 phase 2 test"`
5. 報告: 「CC02 第2次テスト完了」とコメント

エラーがあれば具体的なメッセージを報告してください。
```

#### CC03用 (第1次成功後)

```
**CC03 第2次テスト**

第1次テスト成功おめでとうございます。
次のシンプルなタスクを実行してください：

1. システム状態確認: `git status > git_status.txt`
2. PR状態確認: `gh pr list > pr_status.txt`
3. 結果報告: 上記ファイルの内容を報告
4. コミット: `git add *.txt && git commit -m "CC03 phase 2 test"`
5. 報告: 「CC03 第2次テスト完了」とコメント

エラーがあれば具体的なメッセージを報告してください。
```

## 🔄 第3次回復プロンプト (実用タスクへの移行)

### CC01用 (第2次成功後)

```
**CC01 実用タスク開始**

素晴らしい進捗です。次の実用タスクを実行してください：

1. コンポーネントディレクトリ作成: `mkdir -p frontend/src/components/ui`
2. 基本コンポーネント作成:
   ```bash
   cat > frontend/src/components/ui/Button.tsx << 'EOF'
   interface ButtonProps {
     children: React.ReactNode;
   }
   
   export function Button({ children }: ButtonProps) {
     return <button className="btn">{children}</button>;
   }
   EOF
   ```
3. コミット: `git add frontend/src/components/ && git commit -m "feat: Add basic Button component"`
4. 報告: 「CC01 Buttonコンポーネント基本実装完了」とコメント

このタスクが成功したら、通常の開発タスクへ移行します。
```

### CC02用 (第2次成功後)

```
**CC02 実用タスク開始**

素晴らしい進捗です。次の実用タスクを実行してください：

1. PR状態確認: `gh pr checks 178 | head -5`
2. 結果報告: CI/CDエラーの中から最も簡単なも1つ特定
3. 小修正の実施: 特定したエラーの最小限修正を実行
4. コミット: `git add . && git commit -m "fix: Minor CI/CD error fix"`
5. 報告: 「CC02 小修正完了」とコメント

複雑な修正は避け、最も簡単なも1つのみ実行してください。
```

### CC03用 (第2次成功後)

```
**CC03 実用タスク開始**

素晴らしい進捗です。次の実用タスクを実行してください：

1. CI/CDエラー詳細確認: `gh pr checks 178 | grep -i "error\|fail" | head -3`
2. 最頑出エラー特定: 繰り返し出現するエラーを1つ特定
3. 簡単修正案提示: 特定したエラーの最簡単な修正方法を提示
4. 報告: 「CC03 エラー分析完了」とコメント

複雑な分析は避け、最も明らかなエラーのみに集中してください。
```

## 📊 全体的な効果測定指標

### 成功率ターゲット

```yaml
第1次テスト_成功率:
  target: 80%以上
  measurement: "3エージェント中2件以上成功"

第2次テスト_成功率:
  target: 70%以上
  measurement: "第1次成功エージェントの70%以上が成功"

実用タスク_成功率:
  target: 50%以上
  measurement: "第2次成功エージェントの50%以上が成功"

全体回復率:
  target: 33%以上
  measurement: "3エージェント中1件以上が実用タスクへ復帰"
```

### 継続的改善のためのデータ収集

```yaml
data_collection:
  response_time: "プロンプト送信から最初の応答までの時間"
  success_patterns: "成功したエージェントの共通パターン"
  failure_reasons: "失敗したエージェントの具体的なエラーメッセージ"
  optimal_complexity: "最も効果的なタスクの複雑さレベル"
```

## 🔧 プロンプトの逆索引

### エラータイプ別対応

```yaml
ファイル作成エラー:
  - ディレクトリアクセス権限の問題
  - パスが間違っている
  - ファイルシステムの問題

gitコマンドエラー:
  - コミット権限の問題
  - ブランチ状態の問題
  - マージコンフリクト

エージェント無応答:
  - プロンプトの複雑さを減らす
  - タスクをさらに小さく分割
  - エージェントの状態確認
```

---

**🚑 最優先アクション**: まずCC03から第1次回復プロンプトを実行し、
30分後に効果検証してください。