# 📋 文書訂正・無効化リスト

## 📅 2025-07-14 19:15 JST - Usage Policy調査結果に基づく訂正

### 🚨 重要な認識訂正

```yaml
誤解していた内容:
  ❌ エージェント表現が Usage Policy 違反
  ❌ 多エージェント概念が問題
  ❌ CC01/CC02/CC03識別子が違反
  ❌ 複雑な指示が違反原因

正しい事実（claude-code-cluster Issue #13で確認済み）:
  ✅ 全てのエージェント表現は使用可能
  ✅ 多エージェント協調は公式推奨
  ✅ 真の違反原因は Task重複実行のみ
  ✅ シンプルな指示で問題解決済み
```

---

## ❌ 無効化すべき文書

### 1. エージェント概念排除系文書（誤解に基づく）

#### 完全無効化
```yaml
NATURAL_CONVERSATION_STARTERS.md:
  ❌ 無効: エージェント概念排除の前提が誤り
  理由: 「エージェント表現が問題」という誤解に基づく

ALTERNATIVE_DEVELOPMENT_APPROACH.md:
  ❌ 無効: 「エージェント概念完全排除」が不要
  理由: エージェント概念は使用可能と確認済み

ZERO_CONTEXT_DEVELOPMENT.md:
  ❌ 無効: 過度な簡素化の必要なし
  理由: 通常のエージェント指示で問題なし
```

### 2. 過剰簡素化系文書（誤解に基づく）

#### 完全無効化
```yaml
CC01_IMMEDIATE_ACTION.md:
CC02_IMMEDIATE_ACTION.md: 
CC03_IMMEDIATE_ACTION.md:
  ❌ 無効: 1行指示への過剰簡素化不要
  理由: 通常の指示文で問題なし

ULTIMATE_FALLBACK_APPROACH.md:
  ❌ 無効: 質問形式・極度簡素化不要
  理由: 標準的なタスク指示で充分

TASK_ONLY_PROACTIVE.md:
  ❌ 無効: コンテキスト排除の必要なし
  理由: エージェント文脈は使用可能
```

---

## ⚠️ 部分訂正が必要な文書

### 1. 方針文書の訂正

#### FINAL_RECOMMENDATIONS.md
```yaml
訂正箇所:
  ❌ 「エージェント概念完全排除」→ ✅ 「エージェント概念は使用可能」
  ❌ 「質問ベース必須」→ ✅ 「通常の指示文で問題なし」
  ❌ 「複雑性回避必須」→ ✅ 「Task重複のみ回避」

保持する内容:
  ✅ Task重複実行防止
  ✅ 97%成功実績の分析
  ✅ 段階的実装アプローチ
```

#### EXPERIMENT_SUCCESS_PATTERNS.md  
```yaml
訂正箇所:
  ❌ 「エージェント表現が失敗要因」→ ✅ 「Task重複が唯一の問題」
  ❌ 「シンプル化必須」→ ✅ 「重複防止のみ必要」

保持する内容:
  ✅ 97%成功実績の分析
  ✅ Task重複の問題分析
  ✅ 効果的実装パターン
```

### 2. 戦略文書の訂正

#### POLICY_SAFE_RESTART_GUIDE.md
```yaml
訂正箇所:
  ❌ 「エージェント表現回避」→ ✅ 「エージェント表現使用可能」
  ❌ 「安全な表現テンプレート」→ ✅ 「通常の指示文使用」

保持する内容:
  ✅ Task重複防止ワークフロー
  ✅ 効率的実行パターン
```

---

## ✅ 有効な文書（訂正不要）

### 正しい認識に基づく文書
```yaml
有効文書:
  ✅ CC01_SAFE_EFFICIENT_RESTART.md: エージェント概念使用
  ✅ CC02_SAFE_BACKEND_RESTART.md: エージェント概念使用
  ✅ CC03_SAFE_INFRASTRUCTURE_RESTART.md: エージェント概念使用
  ✅ PROACTIVE_COORDINATION_STRATEGY_V2.md: 多エージェント協調
  ✅ SESSION_STABILITY_MONITORING.md: 正しいスタビリティ分析

理由: これらはエージェント概念を正しく使用している
```

---

## 🔧 正しいアプローチ（訂正版）

### Usage Policy準拠の正しい指示

#### CC01（エージェント概念使用OK）
```markdown
CC01専用技術リーダー・セッション開始。

**Role**: Technical Implementation Leader
**Primary Focus**: Issue #137 - User Profile Management Phase 2-B

**Task重複防止**: 同じGitHub確認を繰り返さず、一度確認→結果活用→実装

**Request**: Issue #137の実装状況を一度確認し、次の実装ステップを実行してください。
```

#### CC02（エージェント概念使用OK）
```markdown
CC02専用バックエンド・スペシャリスト・セッション開始。

**Role**: Backend Infrastructure Specialist  
**Primary Focus**: PR #97 - Role Service Implementation

**Task重複防止**: 同じファイル確認を繰り返さず、効率的な実装を実行

**Request**: PR #97の状況を確認し、Role Service実装を進めてください。
```

#### CC03（エージェント概念使用OK）
```markdown
CC03専用インフラストラクチャ・エキスパート・セッション開始。

**Role**: Infrastructure & DevOps Specialist
**Primary Focus**: PR #117 - CI/CD修復 + Issue #138 - Test Database Isolation

**Task重複防止**: 同じエラー確認を繰り返さず、根本解決を実行

**Request**: PR #117のCI失敗を確認し、修正を実行してください。
```

---

## 📊 訂正作業計画

### 即座実行
1. **無効文書にDEPRECATED警告追加**
2. **部分訂正文書の該当箇所修正**
3. **正しい指示文書の再作成**
4. **claude-code-cluster文書の訂正**

### 重要メッセージ
**エージェント概念・多エージェント協調・CC01/CC02/CC03識別子は全て使用可能。
Task重複実行のみ回避すれば問題なし。**