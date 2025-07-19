# 🔄 エージェント回復プロンプト戦略

**作成日時**: 2025年7月17日 24:00 JST  
**作成者**: Claude Code (CC01) - システム統合担当  
**目的**: 動作中だが指示実行できないエージェントの回復

## 📋 回復アプローチの基本方針

### 段階的回復戦略
1. **Phase 1**: 最小限の生存確認
2. **Phase 2**: 単純な動作確認
3. **Phase 3**: 段階的なタスク復帰
4. **Phase 4**: 通常作業への復帰

### プロンプト設計原則
- **Ultra Simple**: 一つのアクションのみ
- **Clear Success**: 明確な成功基準
- **Immediate**: 即座に実行可能
- **Verifiable**: 結果が確認可能
- **No Dependencies**: 他の作業に依存しない

## 🎯 CC01 回復プロンプト

### Phase 1: 生存確認プロンプト
```markdown
**CC01 緊急確認**

以下の1つのタスクのみを実行してください：

1. `echo "CC01 Active $(date)" > CC01_STATUS.txt`
2. このファイルをgit addしてコミット
3. 「CC01 回復確認」とコメントで報告

他のタスクは一切実行しないでください。
上記のみ実行して結果を報告してください。
```

### Phase 2: 基本動作確認プロンプト
```markdown
**CC01 基本動作確認**

Phase 1が成功した場合のみ実行：

1. `frontend/src/test-file.ts`を作成
2. 内容：`export const test = "CC01 working";`
3. git add, commit, push
4. 「基本動作確認完了」と報告

失敗した場合は「失敗：[理由]」と報告してください。
```

### Phase 3: 段階的タスク復帰プロンプト
```markdown
**CC01 段階的復帰**

Phase 2が成功した場合のみ実行：

1. `frontend/src/components/`ディレクトリを作成
2. `frontend/src/components/Button.tsx`を作成
3. 最小限の内容：
   ```typescript
   export function Button() {
     return <button>Test</button>;
   }
   ```
4. git add, commit, push
5. 「段階的復帰完了」と報告

問題があれば具体的に報告してください。
```

### Phase 4: 通常作業復帰プロンプト
```markdown
**CC01 通常作業復帰**

Phase 3が成功した場合のみ実行：

通常のButton コンポーネント実装を開始してください。
以前の指示に従って作業を継続してください。
```

## 🎯 CC02 回復プロンプト

### Phase 1: 生存確認プロンプト
```markdown
**CC02 緊急確認**

以下の1つのタスクのみを実行してください：

1. `echo "CC02 Active $(date)" > backend/CC02_STATUS.txt`
2. このファイルをgit addしてコミット
3. 「CC02 回復確認」とコメントで報告

他のタスクは一切実行しないでください。
上記のみ実行して結果を報告してください。
```

### Phase 2: 基本動作確認プロンプト
```markdown
**CC02 基本動作確認**

Phase 1が成功した場合のみ実行：

1. `backend/test_cc02.py`を作成
2. 内容：`def test_cc02(): return "CC02 working"`
3. `cd backend && uv run python test_cc02.py`を実行
4. 結果を報告
5. git add, commit, push

失敗した場合は「失敗：[理由]」と報告してください。
```

### Phase 3: CI/CD状況確認プロンプト
```markdown
**CC02 CI/CD状況確認**

Phase 2が成功した場合のみ実行：

1. `gh pr checks 178`を実行
2. 結果を報告
3. 最も簡単に修正できそうなエラーを1つ特定
4. 「CI/CD状況：[結果]、修正候補：[エラー]」と報告

複雑な修正は提案しないでください。
```

### Phase 4: 段階的修正プロンプト
```markdown
**CC02 段階的修正**

Phase 3で修正候補が見つかった場合のみ実行：

特定したエラーの最小限の修正のみを実行してください。
1つのファイルの1つの問題のみを修正してください。
```

## 🎯 CC03 回復プロンプト

### Phase 1: 生存確認プロンプト
```markdown
**CC03 緊急確認**

以下の1つのタスクのみを実行してください：

1. `echo "CC03 Active $(date)" > CC03_STATUS.txt`
2. このファイルをgit addしてコミット
3. 「CC03 回復確認」とコメントで報告

他のタスクは一切実行しないでください。
上記のみ実行して結果を報告してください。
```

### Phase 2: 基本動作確認プロンプト
```markdown
**CC03 基本動作確認**

Phase 1が成功した場合のみ実行：

1. `git status`を実行
2. 結果を報告
3. `gh pr list`を実行
4. 結果を報告
5. 「基本動作確認完了」と報告

失敗した場合は「失敗：[理由]」と報告してください。
```

### Phase 3: CI/CD診断プロンプト
```markdown
**CC03 CI/CD診断**

Phase 2が成功した場合のみ実行：

1. `gh pr checks 178 | head -10`を実行
2. 結果を報告
3. 最も多く出現するエラーパターンを1つ特定
4. 「診断結果：[エラーパターン]」と報告

複雑な分析は不要です。最も明らかなエラーのみ特定してください。
```

### Phase 4: 最小限修正プロンプト
```markdown
**CC03 最小限修正**

Phase 3で明らかなエラーが特定された場合のみ実行：

特定したエラーの最も簡単な修正のみを実行してください。
1つのファイルの1つの設定のみを変更してください。
```

## 🔍 効果検証方法

### 各フェーズの成功基準

#### Phase 1 成功基準
```yaml
CC01:
  - CC01_STATUS.txtが作成されている
  - ファイルに現在日時が記録されている
  - コミットが作成されている
  - エージェントから「CC01 回復確認」の報告

CC02:
  - backend/CC02_STATUS.txtが作成されている
  - ファイルに現在日時が記録されている
  - コミットが作成されている
  - エージェントから「CC02 回復確認」の報告

CC03:
  - CC03_STATUS.txtが作成されている
  - ファイルに現在日時が記録されている
  - コミットが作成されている
  - エージェントから「CC03 回復確認」の報告
```

#### Phase 2 成功基準
```yaml
CC01:
  - frontend/src/test-file.tsが作成されている
  - 指定された内容が記録されている
  - コミットが作成されている
  - エージェントから「基本動作確認完了」の報告

CC02:
  - backend/test_cc02.pyが作成されている
  - Python実行結果が報告されている
  - コミットが作成されている
  - エラーがあれば具体的な理由が報告されている

CC03:
  - git statusの結果が報告されている
  - gh pr listの結果が報告されている
  - エージェントから「基本動作確認完了」の報告
```

### 検証用コマンド

```bash
# Phase 1 検証
echo "=== Phase 1 検証 ==="
ls -la *STATUS.txt backend/CC02_STATUS.txt 2>/dev/null || echo "Status files not found"
git log --oneline -5 | grep -i "cc0[123]" || echo "No agent commits found"

# Phase 2 検証
echo "=== Phase 2 検証 ==="
ls -la frontend/src/test-file.ts backend/test_cc02.py 2>/dev/null || echo "Test files not found"

# Phase 3 検証
echo "=== Phase 3 検証 ==="
ls -la frontend/src/components/ 2>/dev/null || echo "Components directory not found"

# 全体進捗確認
echo "=== 全体進捗 ==="
git log --oneline --since="1 hour ago" | head -10
```

## 📊 プロンプト効果測定

### 測定指標

```yaml
response_time:
  target: "30分以内"
  measurement: "プロンプト送信から最初の応答まで"

success_rate:
  target: "80%以上"
  measurement: "各フェーズの成功率"

completion_rate:
  target: "Phase 3まで到達"
  measurement: "4フェーズ中の到達フェーズ"

communication_clarity:
  target: "明確な状況報告"
  measurement: "エラー理由の具体性"
```

### 失敗時の対応

```yaml
Phase_1_failure:
  - エージェントの基本的な動作に問題
  - 権限やアクセスの問題の可能性
  - より単純なテストが必要

Phase_2_failure:
  - 環境設定の問題
  - 依存関係の問題
  - 作業ディレクトリの問題

Phase_3_failure:
  - 複雑すぎるタスク
  - 前提条件の不足
  - 技術的な制約

Phase_4_failure:
  - 通常作業への復帰に問題
  - 元の指示に問題がある可能性
  - より詳細な分析が必要
```

## 🎯 自動化への展開

### プロンプトテンプレート化

```python
# 将来の自動化用テンプレート
class AgentRecoveryPrompt:
    def __init__(self, agent_id, phase):
        self.agent_id = agent_id
        self.phase = phase
    
    def generate_phase1_prompt(self):
        return f"""
        **{self.agent_id} 緊急確認**
        
        以下の1つのタスクのみを実行してください：
        
        1. `echo "{self.agent_id} Active $(date)" > {self.agent_id}_STATUS.txt`
        2. このファイルをgit addしてコミット
        3. 「{self.agent_id} 回復確認」とコメントで報告
        """
    
    def verify_phase1_success(self):
        # 自動検証ロジック
        pass
```

### 成功パターンの学習

```yaml
learning_data:
  successful_prompts:
    - prompt_text
    - success_rate
    - response_time
    - common_errors
  
  optimization_opportunities:
    - より効果的な指示方法
    - 成功率の高いフレーズ
    - エラー回避パターン
```

## 🔧 実装推奨順序

### 段階的実装

1. **CC03から開始**: CI/CD問題が最も緊急
2. **CC02を続行**: PR修正が次に重要
3. **CC01を最後**: UI作業は並行実行可能

### 並行実行の場合

```yaml
parallel_execution:
  - 全エージェントでPhase 1を同時実行
  - 成功したエージェントのみPhase 2へ
  - 段階的に復帰させる
```

---

**🎯 次のアクション**: まずCC03のPhase 1プロンプトから実行開始