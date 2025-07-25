# プロアクティブ簡潔戦略 - 自走可能な継続開発

## 🎯 核心原則
**シンプル・直接的・単一実行**

## 📋 優先順位マトリクス

### 即座実行（今日）
1. **Issue #137**: Department Management (CC01)
2. **PR #97**: Role Service確認 (CC02)
3. **Issue #138**: UI Component (CC03)

### 短期目標（今週）
1. **Usage最適化**: Issue #12の実装
2. **単一タスク完了**: 各エージェント1タスク
3. **品質保証**: テスト実行と型チェック

### 中期目標（今月）
1. **コスト削減**: 70%削減達成
2. **自動化**: claude-code-clusterフル活用
3. **安定運用**: Usage Policy違反ゼロ

## 🚀 自走可能なワークフロー

### CC01 (Backend) - 継続タスク
```bash
# 日次タスク（1回のみ）
gh issue list --repo itdojp/ITDO_ERP2 --label backend --state open --limit 1

# 実装サイクル
if [ ISSUE_FOUND ]; then
    implement_single_issue
    test_and_verify
    create_pr
fi
```

### CC02 (Database) - 継続タスク
```bash
# 週次最適化（短時間）
analyze_slow_queries --limit 3
optimize_top_query
verify_performance
```

### CC03 (Frontend) - 継続タスク
```bash
# UI改善サイクル
check_lighthouse_score
implement_one_improvement
verify_a11y_compliance
```

## 🔄 自動化された品質保証

### 毎回実行（自動）
```bash
# Pre-commit hooks
- TypeScript型チェック
- ESLint実行
- テスト実行

# Post-implementation
- カバレッジ確認
- パフォーマンステスト
```

## 📊 成功指標（シンプル）

### 日次
- [ ] 1タスク完了/エージェント
- [ ] Usage Policy違反: 0
- [ ] テスト通過率: 100%

### 週次
- [ ] 5タスク完了
- [ ] コスト削減: 前週比10%
- [ ] 品質スコア向上

## 🚫 絶対的禁止事項

1. **タスクの重複実行**: 同じタスクを2回以上実行しない
2. **複雑なフレームワーク**: KISS原則の徹底
3. **長時間分析**: 30分以上の連続作業禁止
4. **メタディスカッション**: 実装に集中

## ✅ エスカレーション（シンプル）

```bash
# 30分ルール
if [ BLOCKED_TIME > 30min ]; then
    escalate "技術的ブロック" "具体的な問題" "試みた解決策"
fi
```

## 🎯 長期ビジョン（3ヶ月）

### 達成目標
1. **完全自動化**: 人間介入最小化
2. **コスト効率**: 90%削減
3. **品質向上**: バグ率50%減
4. **開発速度**: 2倍向上

### 成功の鍵
- **単純さ**: 複雑さを避ける
- **直接性**: 回り道をしない
- **効率性**: 最小労力で最大成果

## 📈 継続的改善（最小限）

### 週次レビュー（5分）
```bash
# 成果確認
count_completed_tasks
calculate_cost_reduction
check_quality_metrics

# 次週計画
select_top_3_priorities
assign_to_agents
```

## 🤖 エージェント行動指針

### 基本ルール
1. **1日1タスク**: 完了を優先
2. **30分制限**: 長時間作業禁止
3. **即座報告**: ブロック時は即エスカレーション
4. **品質維持**: テスト必須

### 成功パターン
- ✅ 小さなタスクを確実に完了
- ✅ 明確な成果物を生成
- ✅ 次のアクションを明示
- ❌ 完璧を求めすぎない

---

🎯 **戦略**: シンプルで効果的な継続開発
🚀 **目標**: 安定した高品質デリバリー
⏰ **期間**: 持続可能な長期運用

**キーワード**: Simple, Direct, Effective